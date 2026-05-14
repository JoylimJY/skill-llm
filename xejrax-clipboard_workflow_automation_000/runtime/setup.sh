#!/bin/bash
set -e

# Start a virtual framebuffer so xclip can connect to an X display
Xvfb :99 -screen 0 1024x768x24 &
sleep 1
export DISPLAY=:99

# Persist DISPLAY for all subsequent processes
echo "export DISPLAY=:99" >> /etc/environment
echo "export DISPLAY=:99" >> /root/.bashrc
echo "export DISPLAY=:99" >> /root/.profile

# Verify xclip works with the virtual display
echo "xclip_test" | xclip -selection clipboard
RESULT=$(xclip -selection clipboard -o)
if [ "$RESULT" = "xclip_test" ]; then
    echo "xclip verified OK with DISPLAY=:99"
else
    echo "WARNING: xclip verification failed. Got: $RESULT"
fi

chmod -R 755 /workspace