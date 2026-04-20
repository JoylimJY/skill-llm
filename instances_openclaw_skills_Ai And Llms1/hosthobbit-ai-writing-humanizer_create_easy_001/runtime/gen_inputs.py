from pathlib import Path

text = """Hi team,

At the end of the day, we need to remember that the project has been delayed, and it is important to note that the issues were caused by a combination of factors. First, the vendor was late. Secondly, the requirements were changing. Finally, the testing phase has been slower than expected.

I hope this helps. Let me know if you have any questions.

Thanks,
Maya"""
Path('input_email.txt').write_text(text, encoding='utf-8')
