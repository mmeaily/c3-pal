// c3-pal: hydration buddy for ESP32-C3 + 0.42" OLED (SSD1306 72x40)
//
//  - Short press BOOT  -> log a drink (cup +1, timer resets)
//  - Long press BOOT   -> reset today's cup count (hold 2 s)
//  - When a drink is due, the screen flashes until you press the button.
//  - The water droplet is the progress bar: it's full right after a drink and
//    drains until the next one is due. Its face shows how hydrated you are.
//
// Power: the screen turns off SCREEN_ON_MS after the last press and the chip
// goes into light sleep (RAM and the timer kept, about 0.1-0.2 mA) until the
// button is pressed or a drink falls due. A press while the screen is off
// only wakes it. When a drink falls due the screen flashes for DUE_SHOW_MS,
// then again every REMIND_EVERY_MS until you drink.
// USB serial stops while the chip sleeps: to flash, tap RST and upload within
// AWAKE_AFTER_BOOT_MS (or hold BOOT and tap RST for download mode).

#include <Arduino.h>
#include <Wire.h>
#include <U8g2lib.h>
#include <Preferences.h>
#include <esp_sleep.h>
#include <driver/gpio.h>

// ------------------------------------------------------------------ config
static const uint32_t DRINK_INTERVAL_MS = 45UL * 60UL * 1000UL;  // remind every 45 min
static const uint8_t  DAILY_GOAL        = 8;                     // cups per day
static const uint32_t LONG_PRESS_MS     = 2000;                  // hold to reset
static const uint32_t FLASH_PERIOD_MS   = 400;                   // invert toggle rate when due
static const uint32_t TOAST_MS          = 1500;                  // "GULP!" / "RESET" duration
static const uint32_t REFILL_MS         = 800;                   // droplet refill animation
static const uint32_t BLINK_EVERY_MS    = 4000;                  // droplet blinks its eyes
static const uint32_t BLINK_LEN_MS      = 150;

// power
static const uint32_t SCREEN_ON_MS        = 15000;               // screen stays on after a press
static const uint32_t DUE_SHOW_MS         = 30000;               // flashing when a drink falls due
static const uint32_t REMIND_EVERY_MS     = 5UL * 60UL * 1000UL; // then again this often until you drink
static const uint32_t AWAKE_AFTER_BOOT_MS = 60000;               // no sleep for this long after power-on (USB upload)
static const uint8_t  CONTRAST            = 128;                 // 0..255; the OLED's current goes with it
static const uint32_t CPU_MHZ             = 80;                  // 80 is the lowest that keeps USB working
static const uint32_t FRAME_MS            = 100;                 // redraw rate with the screen on
static const uint32_t FRAME_ANIM_MS       = 40;                  // ... during the refill animation

// Pins for the common "ESP32-C3 0.42 OLED" board
#define PIN_SDA 5
#define PIN_SCL 6
#define PIN_BTN 9   // BOOT button, active low

// ------------------------------------------------------------------ globals
// The "ER" 72x40 constructor handles the panel's offset inside the 128x64 controller.
// Pins are NOT passed here: on ESP32 that makes U8g2 call Wire.begin() itself with
// an ambiguous overload. We call Wire.begin(SDA, SCL) explicitly in setup() instead.
// Screen rotation: U8G2_R0 in the bar (USB-C down), U8G2_R2 in the boot,
// where the board stands USB-C up (env:boot sets it).
#ifndef C3PAL_ROTATION
#define C3PAL_ROTATION U8G2_R0
#endif
U8G2_SSD1306_72X40_ER_F_HW_I2C u8g2(C3PAL_ROTATION, U8X8_PIN_NONE);
Preferences prefs;

enum Mood { M_GREAT, M_OK, M_THIRSTY, M_DUE, M_GULP, M_RESET };

static uint8_t  cups        = 0;
static uint32_t lastDrinkMs = 0;
static uint32_t toastUntil  = 0;
static Mood     toastMood   = M_GULP;
static float    refillFrom  = 0;   // water level when the last drink was logged
static bool     inverted    = false;
static bool     screenOn      = true;
static uint32_t screenOnUntil = 0;
static uint32_t nextAlertMs   = 0;      // when the screen next wakes to flash "DRINK!"
static bool     swallowPress  = false;  // the press that woke the screen does nothing else

// ------------------------------------------------------------------ helpers
static float waterLeft(uint32_t now) {  // 1.0 = just drank, 0.0 = due
  uint32_t el = now - lastDrinkMs;
  if (el >= DRINK_INTERVAL_MS) return 0;
  return 1.0f - (float)el / DRINK_INTERVAL_MS;
}

static void saveCups() {
  prefs.putUChar("cups", cups);
}

static void setInverted(bool inv) {
  if (inv == inverted) return;
  inverted = inv;
  u8g2.sendF("c", inv ? 0xA7 : 0xA6);  // SSD1306 invert / normal display
}

// Keep the screen on until at least now + ms.
static void wakeScreen(uint32_t now, uint32_t ms) {
  if (!screenOn) {
    u8g2.setPowerSave(0);
    screenOn = true;
  }
  if ((int32_t)(now + ms - screenOnUntil) > 0) screenOnUntil = now + ms;
}

static void showToast(Mood m, uint32_t now) {
  toastMood  = m;
  toastUntil = now + TOAST_MS;
}

static void onDrink(uint32_t now) {
  refillFrom = waterLeft(now);
  if (cups < 99) cups++;
  lastDrinkMs = now;
  nextAlertMs = now + DRINK_INTERVAL_MS;
  saveCups();
  showToast(M_GULP, now);
  Serial.printf("Drink! cups=%u\n", cups);
}

static void onReset(uint32_t now) {
  refillFrom = waterLeft(now);
  cups = 0;
  lastDrinkMs = now;
  nextAlertMs = now + DRINK_INTERVAL_MS;
  saveCups();
  showToast(M_RESET, now);
  Serial.println("Cup count reset");
}

// ------------------------------------------------------------------ button
static bool btnDown = false;  // a press is in progress (keeps the screen awake)

static void pollButton(uint32_t now) {
  static bool     lastRaw    = HIGH;
  static uint32_t lastChange = 0;
  static uint32_t downSince  = 0;
  static bool     longFired  = false;
  bool& down = btnDown;

  bool raw = digitalRead(PIN_BTN);
  if (raw != lastRaw) { lastRaw = raw; lastChange = now; }
  if (now - lastChange < 30) return;  // debounce

  bool pressed = (raw == LOW);
  if (swallowPress) {                 // the press that woke the screen
    if (!pressed) { swallowPress = false; down = false; }
    return;
  }
  if (pressed && !screenOn) {         // screen off: this press only wakes it
    swallowPress = true;
    wakeScreen(now, SCREEN_ON_MS);
    return;
  }
  if (pressed) wakeScreen(now, SCREEN_ON_MS);
  if (pressed && !down) {
    down = true; downSince = now; longFired = false;
  } else if (pressed && down && !longFired && now - downSince >= LONG_PRESS_MS) {
    longFired = true;
    onReset(now);
  } else if (!pressed && down) {
    down = false;
    if (!longFired) onDrink(now);
  }
}

// ------------------------------------------------------------------ mood
static bool toastActive(uint32_t now) { return (int32_t)(toastUntil - now) > 0; }

static Mood currentMood(uint32_t now) {
  if (toastActive(now)) return toastMood;
  uint32_t el = now - lastDrinkMs;
  if (el >= DRINK_INTERVAL_MS)        return M_DUE;
  if (el < DRINK_INTERVAL_MS / 3)     return M_GREAT;
  if (el < DRINK_INTERVAL_MS * 2 / 3) return M_OK;
  return M_THIRSTY;
}

// ------------------------------------------------------------------ droplet
// Layout: droplet on the left (30x40 px), text on the right (x = 30..71).
static const float DROP_CX  = 15.0f;  // horizontal centre
static const float DROP_TIP = 0.0f;   // y of the pointed top
static const float DROP_CY  = 26.0f;  // centre of the round bottom
static const float DROP_R   = 13.0f;  // radius of the round bottom
static const float WALL     = 1.6f;   // outline thickness

static float hwOuter[40], hwInner[40];  // half-width of each row (-1 = outside)
static float cumArea[41];               // inner area from row y down to the bottom

// Teardrop: a sine-shaped point on top of a circle.
static float shapeHW(float y, float tip, float cy, float r) {
  if (y < tip) return -1;
  if (y <= cy) return r * sinf((y - tip) / (cy - tip) * PI / 2);
  float d = y - cy;
  return d > r ? -1 : sqrtf(r * r - d * d);
}

static void initDropShape() {
  float innerTop = DROP_TIP + WALL * 1.6f;
  for (int y = 0; y < 40; y++) {
    hwOuter[y] = shapeHW(y, DROP_TIP, DROP_CY, DROP_R);
    hwInner[y] = shapeHW(y, innerTop, DROP_CY, DROP_R - WALL);
  }
  cumArea[40] = 0;
  for (int y = 39; y >= 0; y--)
    cumArea[y] = cumArea[y + 1] + (hwInner[y] > 0 ? 2 * hwInner[y] : 0);
}

// Water surface y for a fill level, by area, so "half left" looks half full.
static float surfaceFor(float level) {
  float target = level * cumArea[0];
  for (int y = 39; y >= 0; y--) {
    if (cumArea[y] >= target) {
      float w = cumArea[y] - cumArea[y + 1];
      return y + 1 - (w > 0 ? (target - cumArea[y + 1]) / w : 0);
    }
  }
  return 0;
}

static void span(float hw, int8_t ox, int& x0, int& x1) {
  x0 = (int)lroundf(DROP_CX - hw) + ox;
  x1 = (int)lroundf(DROP_CX + hw) - 1 + ox;
}

// level: 0..1 water fill, waveAmp: surface wobble in px
static void drawDroplet(float level, float waveAmp, int8_t ox, uint32_t now) {
  float surface = surfaceFor(level);
  float phase   = now * 0.004f;

  for (int y = 0; y < 40; y++) {
    int x0, x1;
    if (hwOuter[y] < 0) continue;
    span(hwOuter[y], ox, x0, x1);
    if (x1 >= x0) { u8g2.setDrawColor(1); u8g2.drawHLine(x0, y, x1 - x0 + 1); }

    if (hwInner[y] < 0) continue;
    span(hwInner[y], ox, x0, x1);
    if (x1 < x0) continue;
    u8g2.setDrawColor(0);
    u8g2.drawHLine(x0, y, x1 - x0 + 1);  // hollow it out

    if (level <= 0) continue;
    u8g2.setDrawColor(1);                 // pour the water in
    for (int x = x0; x <= x1; x++) {
      float s = surface + sinf(x * 0.55f + phase) * waveAmp;
      if (y >= s) u8g2.drawPixel(x, y);
    }
  }
  u8g2.setDrawColor(1);
}

// Face uses XOR so it stays visible over both water and empty space.
static void drawFace(Mood m, int8_t ox, uint32_t now) {
  const char* eyes;
  const char* mouth;
  switch (m) {
    case M_GREAT:   eyes = "^ ^"; mouth = "\\_/"; break;  // big smile
    case M_OK:      eyes = "o o"; mouth = " u "; break;   // content
    case M_THIRSTY: eyes = "- -"; mouth = " ~ "; break;   // meh
    case M_DUE:     eyes = "x x"; mouth = "/~\\"; break;  // parched
    case M_GULP:    eyes = "^ ^"; mouth = "(O)"; break;   // gulping
    case M_RESET:
    default:        eyes = "o o"; mouth = " o "; break;
  }
  if ((m == M_GREAT || m == M_OK) && (now % BLINK_EVERY_MS) < BLINK_LEN_MS) eyes = "- -";

  u8g2.setFont(u8g2_font_5x7_tf);
  u8g2.setFontMode(1);
  u8g2.setDrawColor(2);
  u8g2.drawStr(8 + ox, 19, eyes);
  u8g2.drawStr(8 + ox, 27, mouth);
  u8g2.setDrawColor(1);
  u8g2.setFontMode(0);

  // sweat drop next to the tip when thirsty
  if (m == M_THIRSTY || m == M_DUE) {
    int x = 24 + ox;
    u8g2.drawPixel(x + 1, 4);
    u8g2.drawHLine(x, 5, 3);
    u8g2.drawHLine(x, 6, 3);
    u8g2.drawPixel(x + 1, 7);
  }
}

// ------------------------------------------------------------------ text
static const uint8_t PANEL_X = 30, PANEL_W = 42;  // text panel

static void drawCentered(int y, const char* s) {
  int w = u8g2.getStrWidth(s);
  u8g2.drawStr(PANEL_X + (PANEL_W - w) / 2, y, s);
}

static void drawInfo(Mood m, uint32_t now) {
  const char* label;
  switch (m) {
    case M_GREAT:   label = "GREAT!";  break;
    case M_OK:      label = "GOOD";    break;
    case M_THIRSTY: label = "THIRSTY"; break;
    case M_DUE:     label = "DRINK!";  break;
    case M_GULP:    label = "GULP!";   break;
    default:        label = "RESET";   break;
  }
  if ((m == M_GREAT || m == M_OK) && cups >= DAILY_GOAL) label = "GOAL!";

  u8g2.setFont(u8g2_font_6x10_tf);
  drawCentered(0, label);

  char buf[12];
  snprintf(buf, sizeof buf, "%u/%u", cups, DAILY_GOAL);
  u8g2.setFont(u8g2_font_helvB12_tr);
  drawCentered(12, buf);

  uint32_t el = now - lastDrinkMs;
  if (el < DRINK_INTERVAL_MS) {
    uint32_t left = (DRINK_INTERVAL_MS - el) / 1000;
    if (left >= 60) snprintf(buf, sizeof buf, "in %lum", (unsigned long)(left / 60));
    else            snprintf(buf, sizeof buf, "in %lus", (unsigned long)left);
  } else {
    snprintf(buf, sizeof buf, "+%lum", (unsigned long)((el - DRINK_INTERVAL_MS) / 60000));
  }
  u8g2.setFont(u8g2_font_6x10_tf);
  drawCentered(30, buf);
}

// ------------------------------------------------------------------ frame
static void render(uint32_t now) {
  Mood m = currentMood(now);

  // flash the whole screen while a drink is overdue
  setInverted(m == M_DUE && (now / FLASH_PERIOD_MS) % 2);

  float level   = waterLeft(now);
  float waveAmp = (level > 0.03f && level < 0.97f) ? 0.8f : 0;

  // refill animation right after a drink / reset
  uint32_t sinceToast = now - (toastUntil - TOAST_MS);
  if (toastActive(now) && sinceToast < REFILL_MS) {
    float t = (float)sinceToast / REFILL_MS;
    t = 1 - (1 - t) * (1 - t);  // ease out
    level   = refillFrom + (1 - refillFrom) * t;
    waveAmp = 1.8f;
  }

  int8_t ox = (m == M_DUE && (now / 600) % 2) ? 1 : 0;  // parched droplet wobbles

  u8g2.clearBuffer();
  drawDroplet(level, waveAmp, ox, now);
  drawFace(m, ox, now);
  drawInfo(m, now);
  u8g2.sendBuffer();
}

static void splash() {
  u8g2.clearBuffer();
  drawDroplet(1.0f, 0, 0, 0);
  drawFace(M_GREAT, 0, 1000);
  u8g2.setFont(u8g2_font_6x10_tf);
  drawCentered(8, "c3-pal");
  drawCentered(22, "hi! :)");
  u8g2.sendBuffer();
  delay(1500);
}

// ------------------------------------------------------------------ main
// Screen off, chip in light sleep until the button or the next alert.
static void sleepUntilNeeded(uint32_t now) {
  int32_t wait = (int32_t)(nextAlertMs - now);
  if (wait < 1) return;
  esp_sleep_enable_timer_wakeup((uint64_t)wait * 1000ULL);
  gpio_wakeup_enable((gpio_num_t)PIN_BTN, GPIO_INTR_LOW_LEVEL);
  esp_sleep_enable_gpio_wakeup();
  esp_light_sleep_start();
  gpio_wakeup_disable((gpio_num_t)PIN_BTN);
  if (esp_sleep_get_wakeup_cause() == ESP_SLEEP_WAKEUP_GPIO) {
    swallowPress = true;
    wakeScreen(millis(), SCREEN_ON_MS);
  }
}

void setup() {
  setCpuFrequencyMhz(CPU_MHZ);
  Serial.begin(115200);
  Serial.setTxTimeoutMs(0);  // don't stall on prints with no USB host
  pinMode(PIN_BTN, INPUT_PULLUP);

  Wire.begin(PIN_SDA, PIN_SCL);
  u8g2.setBusClock(400000);  // shorter I2C transfers
  u8g2.begin();
  u8g2.setContrast(CONTRAST);
  u8g2.setFontPosTop();

  prefs.begin("c3pal", false);
  cups = prefs.getUChar("cups", 0);

  initDropShape();
  splash();
  lastDrinkMs = millis();  // timer starts at power-on
  nextAlertMs = lastDrinkMs + DRINK_INTERVAL_MS;
  wakeScreen(lastDrinkMs, SCREEN_ON_MS);
  Serial.printf("c3-pal ready, cups=%u\n", cups);
}

void loop() {
  uint32_t now = millis();

  // a drink falls due (and every REMIND_EVERY_MS after): flash for a while
  if ((int32_t)(now - nextAlertMs) >= 0) {
    wakeScreen(now, DUE_SHOW_MS);
    nextAlertMs = now + DUE_SHOW_MS + REMIND_EVERY_MS;
  }

  pollButton(now);

  if (screenOn) {
    static uint32_t lastFrame = 0;
    bool anim = toastActive(now) && now - (toastUntil - TOAST_MS) < REFILL_MS;
    if (now - lastFrame >= (anim ? FRAME_ANIM_MS : FRAME_MS)) {
      lastFrame = now;
      render(now);
    }
    bool idle = (int32_t)(now - screenOnUntil) >= 0 && !toastActive(now) &&
                !btnDown && !swallowPress && digitalRead(PIN_BTN) == HIGH;
    if (idle) {
      setInverted(false);
      u8g2.setPowerSave(1);  // OLED off (a few uA)
      screenOn = false;
    }
    delay(10);
    return;
  }

  if (now < AWAKE_AFTER_BOOT_MS) { delay(10); return; }  // let USB uploads work after a reset
  sleepUntilNeeded(now);
}
