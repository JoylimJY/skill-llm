#!/bin/bash
set -e

echo "Setting up workspace permissions..."
chmod -R 755 /workspace

# Create the SKILL.md with the references directory structure
mkdir -p /workspace/skill_refs/references

cat > /workspace/skill_refs/SKILL.md << 'SKILLEOF'
# Anki Card Generator

Generate high-quality Anki cards based on LessWrong best practices and simple-anki-sync format.

## Output Format

Use simple-anki-sync format:

\`\`\`markdown
#anki/[domain]/[topic]

| [Question] |
| ---------- |
| [Core answer]<br><br><small>💡 [Supplementary info]</small> |
\`\`\`

### Format Options

**Option A (Recommended)**: HTML tags

\`\`\`markdown
| 唐朝建立时间 |
| ---------- |
| 618年，李渊建立<br><br><small>💡 隋末农民起义后起兵</small> |
\`\`\`

## Atomization Rules

### Word Limits

- **English**: Max 9 words, absolute limit 18 words
- **Chinese**: Recommended 15-20 characters, absolute limit 30-35 characters
- **Max items**: 3 bullet points per card

### Core Principle

If a card can be split into two shorter cards, split it.

## Question Design

### Standardized Templates

- **Time**: "X 时间" (not "X发生于何时？")
- **Definition**: "X definition" (not "What is X?")
- **Person**: "who X" (not "谁做了X？")
- **Pros/Cons**: "X pros/cons" (not "What are the advantages of X?")

### Key Rules

- Match real-world recall scenarios
- Use plain, unremarkable wording
- Avoid words in question that appear in answer
- Keep all critical info in answer, not question

## Answer Construction

### Core Answer

- Strictly follow word limits
- Answer should be meaningful without the question
- All key information in answer

### Supplementary Info (Optional)

Format: \`<br><br><small>💡 content</small>\`

**Emoji Guide**:

- 💡 Fun fact / trivia
- 📝 Note / explanation
- 🔗 Related concept
- ⚡ Tip / key point
- 📊 Data / statistics
- 📅 Date / timeline

Keep supplementary info to 10-20 characters.

### Handle System

Use \`>\` to reference related cards:

\`\`\`markdown
| 牛顿贡献 |
| ------- |
| >运动定律 >万有引力 >微积分发展 |
\`\`\`

## Tag Naming

Use English tags: \`#anki/[domain]/[topic]\`

Common domains: history, programming, language, science, mathematics, psychology, economics, philosophy, medicine, art

## Detail Levels

- **Level 1**: Basic concept (core answer)
- **Level 2**: Detailed info (supplementary section)
- **Level 3**: Advanced details (create separate cards)
SKILLEOF

echo "Setup complete."