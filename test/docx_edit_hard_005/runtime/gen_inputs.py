import docx
from docx.oxml.shared import OxmlElement, qn

def add_comment_run(paragraph, comment_id, text):
    # Create comment range start element
    comment_range_start = OxmlElement('w:commentRangeStart')
    comment_range_start.set(qn('w:id'), str(comment_id))

    # Create comment range end element
    comment_range_end = OxmlElement('w:commentRangeEnd')
    comment_range_end.set(qn('w:id'), str(comment_id))

    # Create comment reference run
    comment_reference = OxmlElement('w:r')
    comment_reference_run_prop = OxmlElement('w:rPr')
    comment_reference_style = OxmlElement('w:rStyle')
    comment_reference_style.set(qn('w:val'), 'CommentReference')
    comment_reference_run_prop.append(comment_reference_style)
    comment_reference.append(comment_reference_run_prop)
    comment_reference_ref = OxmlElement('w:commentReference')
    comment_reference_ref.set(qn('w:id'), str(comment_id))
    comment_reference.append(comment_reference_ref)

    # Insert the comment range start before the text runs
    paragraph._p.insert(0, comment_range_start)

    # Append the comment range end and reference after the text runs
    paragraph._p.append(comment_range_end)
    paragraph._p.append(comment_reference)


def create_initial_doc():
    doc = docx.Document()

    # Add some paragraphs
    doc.add_paragraph('Contract agreement between Company A and Company B.')
    para_clause = doc.add_paragraph('Payment terms: net 30 days.')

    # Add a tracked change deletion + insertion to simulate some edits
    # Because python-docx does not support tracked changes directly,
    # we just add text; tracked changes will be tested by unpack/edit eval

    # Add heading style
    doc.add_paragraph('Terms and Conditions:', style='Heading 1')

    doc.save('contract.docx')


if __name__ == '__main__':
    create_initial_doc()
