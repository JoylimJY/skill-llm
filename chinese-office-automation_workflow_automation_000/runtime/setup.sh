#!/bin/bash
set -e

# Make all scripts executable
chmod +x /workspace/scripts/workday_check.py
chmod +x /workspace/scripts/lunar_convert.py
chmod +x /workspace/scripts/number_to_chinese.py
chmod +x /workspace/scripts/pinyin_convert.py

# Verify dependencies are available
python3 -c "import zhdate; print('zhdate OK')"
python3 -c "from pypinyin import pinyin; print('pypinyin OK')"
python3 -c "import opencc; print('opencc OK')" 2>/dev/null || python3 -c "import opencc; print('opencc OK')"

# Test that scripts work
python3 /workspace/scripts/workday_check.py "2025-03-17" 
python3 /workspace/scripts/lunar_convert.py "2025-03-17"
python3 /workspace/scripts/number_to_chinese.py "12345.67"

echo "Setup complete. All scripts functional."