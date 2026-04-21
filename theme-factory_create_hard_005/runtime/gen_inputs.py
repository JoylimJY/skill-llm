import textwrap

presentation_md = textwrap.dedent("""
# Slide 1: Introduction

Welcome to the presentation on Theme Factory.

---

# Slide 2: Problem Statement

We need consistent, professional theming for all our artifacts.

---

# Slide 3: Current Themes

There are 10 preset themes such as Ocean Depths, Sunset Boulevard, and more.

---

# Slide 4: Need for Custom Theme

Sometimes, a new look better fits the audience or occasion.

---

# Slide 5: Conclusion

Custom themes allow flexibility and brand alignment.
""")

with open("presentation.md", "w", encoding="utf-8") as f:
    f.write(presentation_md)
