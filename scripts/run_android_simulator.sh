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

echo "🛡️ [Suraksha] Initializing Android Phone Simulator..."

# 1. Check if an Android device or emulator is already running
RUNNING_DEVICE=$($ADB devices | grep -E "device$" | grep -v "emulator-.*" | head -n 1 | awk '{print $1}' || true)
RUNNING_EMU=$($ADB devices | grep -E "emulator-.*device$" | head -n 1 | awk '{print $1}' || true)

if [ -n "$RUNNING_DEVICE" ]; then
    echo "📱 Detected connected physical Android device: $RUNNING_DEVICE"
elif [ -n "$RUNNING_EMU" ]; then
    echo "⚡ Detected already running Android emulator: $RUNNING_EMU"
else
    echo "🔍 Checking for existing phone AVDs..."
    AVAILABLE_AVDS=$($EMULATOR -list-avds 2>/dev/null || true)

    if echo "$AVAILABLE_AVDS" | grep -v -i "wear" | grep -q "$AVD_NAME"; then
        echo "✅ Found existing phone AVD: $AVD_NAME"
    else
        echo "⚙️ No phone AVD found. Auto-provisioning Google Pixel 8 Pro AVD..."
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
        echo "✅ Successfully provisioned ${AVD_NAME} phone AVD!"
    fi

    echo "🚀 Booting Android Phone Simulator (${AVD_NAME})..."
    # Clean any stale locks from previous aborted boots
    rm -f "$HOME/.android/avd/${AVD_NAME}.avd/"*.lock 2>/dev/null || true

    "$EMULATOR" -avd "$AVD_NAME" -gpu auto -no-snapshot-load > /dev/null 2>&1 &
    
    echo "⏳ Waiting for Android Phone Simulator to complete boot sequence..."
    "$ADB" wait-for-device
    
    # Wait until boot completed property is 1
    BOOT_TIMEOUT=120
    ELAPSED=0
    while [ "$($ADB shell getprop sys.boot_completed 2>/dev/null | tr -d '\r')" != "1" ]; do
        sleep 2
        ELAPSED=$((ELAPSED + 2))
        if [ $ELAPSED -ge $BOOT_TIMEOUT ]; then
            echo "⚠️ Simulator boot timeout reached. Proceeding anyway..."
            break
        fi
        echo -n "."
    done
    echo ""
    echo "🎉 Android Phone Simulator is fully booted and online!"
fi

# 2. Reverse ports so the emulator can talk directly to localhost:8000 and localhost:8082
echo "🔗 Setting up reverse port proxies (8000, 8082)..."
$ADB reverse tcp:8000 tcp:8000 2>/dev/null || true
$ADB reverse tcp:8082 tcp:8082 2>/dev/null || true

# 3. Launch Expo development server and open on the phone simulator
echo "📲 Launching Suraksha Mobile App on Simulator..."
cd "$PROJECT_ROOT/apps/mobile"
npx expo start --android --port 8082
