#!/usr/bin/env bash
set -e

# ==============================================================================
# Suraksha Automated Android Phone Simulator Launcher & App Deployer
# Ensures a phone AVD exists, boots it, sets up port forwarding, and launches the app.
# ==============================================================================

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export ANDROID_HOME="${ANDROID_HOME:-/Users/dpcubed/Library/Android/sdk}"
export PATH="$PATH:$ANDROID_HOME/platform-tools:$ANDROID_HOME/emulator"

ADB="$ANDROID_HOME/platform-tools/adb"
EMULATOR="$ANDROID_HOME/emulator/emulator"
AVD_NAME="Pixel_8_Pro"

# Allow selecting foldable device vs standard phone
if [ "$1" == "--fold" ] || [ "$1" == "fold" ] || [ "$1" == "--pixel-fold" ]; then
    AVD_NAME="Pixel_Fold"
elif [ "$1" == "--phone" ] || [ "$1" == "phone" ] || [ "$1" == "--pixel8" ]; then
    AVD_NAME="Pixel_8_Pro"
fi

echo "🛡️ [Suraksha] Initializing Android Simulator ($AVD_NAME)..."

# 1. Discover running devices or emulators
RUNNING_DEVICE=$($ADB devices 2>/dev/null | grep -E "device$" | grep -v "emulator-.*" | head -n 1 | awk '{print $1}' || true)
RUNNING_EMU=$($ADB devices 2>/dev/null | grep -E "emulator-.*device$" | head -n 1 | awk '{print $1}' || true)

TARGET_DEVICE=""

if [ -n "$RUNNING_DEVICE" ]; then
    TARGET_DEVICE="$RUNNING_DEVICE"
    echo "📱 Detected connected physical Android device: $TARGET_DEVICE"
elif [ -n "$RUNNING_EMU" ]; then
    RUNNING_AVD=$($ADB -s "$RUNNING_EMU" emu avd name 2>/dev/null | head -n 1 | tr -d '\r' || true)
    
    # If the user explicitly requested a different device type than what is running, kill and switch
    if [ -n "$1" ] && [ -n "$RUNNING_AVD" ] && [ "$RUNNING_AVD" != "$AVD_NAME" ]; then
        echo "🔄 Requested $AVD_NAME but $RUNNING_AVD ($RUNNING_EMU) is running. Switching emulator..."
        $ADB -s "$RUNNING_EMU" emu kill 2>/dev/null || true
        sleep 2
        RUNNING_EMU=""
    else
        TARGET_DEVICE="$RUNNING_EMU"
        echo "⚡ Detected already running Android emulator: $TARGET_DEVICE (${RUNNING_AVD:-$AVD_NAME})"
    fi
fi

# 2. If no device or matching emulator is online, boot one
if [ -z "$TARGET_DEVICE" ]; then
    # Clean up any dangling/offline emulators to prevent 'more than one device' collisions
    ALL_EMUS=$($ADB devices 2>/dev/null | grep -E "^emulator-[0-9]+" | awk '{print $1}' || true)
    for emu in $ALL_EMUS; do
        echo "🧹 Cleaning up dangling emulator: $emu"
        $ADB -s "$emu" emu kill 2>/dev/null || true
    done
    sleep 1

    echo "🔍 Checking for existing AVD: $AVD_NAME..."
    AVAILABLE_AVDS=$($EMULATOR -list-avds 2>/dev/null || true)

    if echo "$AVAILABLE_AVDS" | grep -q "$AVD_NAME"; then
        echo "✅ Found existing AVD: $AVD_NAME"
    else
        echo "⚙️ No $AVD_NAME AVD found. Auto-provisioning Google $AVD_NAME AVD..."
        mkdir -p "$HOME/.android/avd/${AVD_NAME}.avd"

        cat << EOF > "$HOME/.android/avd/${AVD_NAME}.ini"
avd.ini.encoding=UTF-8
path=$HOME/.android/avd/${AVD_NAME}.avd
path.rel=avd/${AVD_NAME}.avd
target=android-37.0
EOF

        cat << EOF > "$HOME/.android/avd/${AVD_NAME}.avd/config.ini"
AvdId=${AVD_NAME}
PlayStore.enabled=true
abi.type=arm64-v8a
avd.ini.displayname=Pixel 8 Pro
avd.ini.encoding=UTF-8
disk.dataPartition.size=2G
fastboot.forceFastBoot=yes
hw.accelerometer=yes
hw.audioInput=yes
hw.battery=yes
hw.camera.back=virtualscene
hw.camera.front=emulated
hw.cpu.arch=arm64
hw.cpu.ncore=4
hw.device.manufacturer=Google
hw.device.name=pixel_8_pro
hw.gps=yes
hw.gpu.enabled=yes
hw.gpu.mode=auto
hw.gyroscope=yes
hw.initialOrientation=portrait
hw.keyboard=yes
hw.lcd.density=480
hw.lcd.height=2992
hw.lcd.width=1344
hw.mainKeys=no
hw.ramSize=2048
hw.sdCard=yes
hw.sensors.light=yes
hw.sensors.magnetic_field=yes
hw.sensors.orientation=yes
hw.sensors.proximity=yes
image.sysdir.1=system-images/android-37.0/google_apis_playstore/arm64-v8a/
runtime.network.latency=none
runtime.network.speed=full
showDeviceFrame=yes
skin.dynamic=yes
skin.name=pixel_8_pro
skin.path=$ANDROID_HOME/skins/pixel_8_pro
tag.display=Google Play
tag.displaynames=Google Play
tag.id=google_apis_playstore
EOF
        echo "✅ Successfully provisioned ${AVD_NAME} AVD!"
    fi

    echo "🚀 Booting Android Simulator (${AVD_NAME})..."
    rm -f "$HOME/.android/avd/${AVD_NAME}.avd/"*.lock 2>/dev/null || true

    TARGET_DEVICE="emulator-5554"
    "$EMULATOR" -avd "$AVD_NAME" -port 5554 -gpu auto > /dev/null 2>&1 &
    
    echo "⏳ Waiting for Android Simulator ($TARGET_DEVICE) to complete boot sequence..."
    "$ADB" -s "$TARGET_DEVICE" wait-for-device
    
    BOOT_TIMEOUT=120
    ELAPSED=0
    while [ "$($ADB -s "$TARGET_DEVICE" shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" != "1" ]; do
        sleep 2
        ELAPSED=$((ELAPSED + 2))
        if [ $ELAPSED -ge $BOOT_TIMEOUT ]; then
            echo "⚠️ Simulator boot timeout reached. Proceeding anyway..."
            break
        fi
        echo -n "."
    done
    echo ""
    echo "🎉 Android Simulator ($TARGET_DEVICE) is fully booted and online!"
fi

# Export target device so Expo and ADB automatically bind to this device
export ANDROID_SERIAL="$TARGET_DEVICE"

# 3. Reverse ports so the emulator can talk directly to localhost:8000 and localhost:8082
echo "🔗 Setting up reverse port proxies on $TARGET_DEVICE (8000, 8082)..."
$ADB -s "$TARGET_DEVICE" reverse tcp:8000 tcp:8000 2>/dev/null || true
$ADB -s "$TARGET_DEVICE" reverse tcp:8082 tcp:8082 2>/dev/null || true

# 4. Launch Expo development server and open on the simulator
echo "📲 Launching Suraksha Mobile App on $TARGET_DEVICE..."
ulimit -n 65536 2>/dev/null || ulimit -n 10240 2>/dev/null || true

cd "$PROJECT_ROOT/apps/mobile"
npx expo start --android --port 8082
