import yaml
import pandas as pd
import xlsxwriter
import click
from pathlib import Path

def calculate_linear_scores(scale_list):
    n = len(scale_list)
    if n <= 1: return {scale_list[0]: 1.0} if n == 1 else {}
    return {item: round(1.0 - (i / (n - 1)), 2) for i, item in enumerate(scale_list)}

def convert_yaml_to_protected_excel(yaml_file, output_file):
    with open(yaml_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f)

    main_rows = []
    lookup_rows = []
    dropdown_map = {}
    guidance_map = {}
    current_row_index = 0

    # 1. Process Data
    for category in data.get('categories', []):
        cat_name = category.get('category')
        for req in category.get('requirements', []):
            req_id = req.get('id')
            evidence = req.get('evidence_examples', [])
            evidence_str = "\n".join([f"• {item}" for item in evidence]) if isinstance(evidence, list) else evidence

            # Scoring Logic
            scale = req.get('assessment_scale', [])
            score_map = req.get('scoring') if req.get('scoring') else calculate_linear_scores(scale)

            for option, score_val in score_map.items():
                lookup_rows.append({'Key': f"{req_id}_{option}", 'Score': score_val})

            main_rows.append({
                'Category': cat_name, 'ID': req_id, 'Title': req.get('title'),
                'Requirement': req.get('requirement'), 'Rationale': req.get('rationale'),
                'Priority': req.get('priority'), 'Weight': req.get('weight', 1),
                'Evidence Examples': evidence_str, 'Assessment': '',
                'Raw Score': '', 'Weighted Score': '', 'Notes': ''
            })
            dropdown_map[current_row_index] = scale
            guidance_map[current_row_index] = req.get('assessment_guidance')
            current_row_index += 1

    # 2. Setup Excel Writer
    writer = pd.ExcelWriter(output_file, engine='xlsxwriter')
    workbook = writer.book

    # 3. Create Hidden Score_Ref Sheet
    df_lookup = pd.DataFrame(lookup_rows)
    df_lookup.to_excel(writer, sheet_name='Score_Ref', index=False)
    writer.sheets['Score_Ref'].hide()

    # 4. Create Main Audit Sheet
    sheet_name = 'Audit Checklist'
    df_main = pd.DataFrame(main_rows)
    df_main.to_excel(writer, sheet_name=sheet_name, index=False, startrow=1, header=False)
    worksheet = writer.sheets[sheet_name]
    worksheet.activate() # Ensure this is the first sheet seen

    # 5. Formats
    header_fmt = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#4F81BD', 'font_color': 'white', 'border': 1})
    # LOCKED FORMATS (Default)
    locked_text = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1, 'locked': True})
    locked_calc = workbook.add_format({'valign': 'top', 'align': 'center', 'border': 1, 'bg_color': '#E6E6E6', 'locked': True})
    # UNLOCKED FORMATS (User can edit)
    unlocked_input = workbook.add_format({'text_wrap': True, 'valign': 'top', 'border': 1, 'bg_color': '#FFF2CC', 'locked': False})

    # 6. Apply Formatting and Protection
    headers = list(df_main.columns)
    for col_num, value in enumerate(headers):
        worksheet.write(0, col_num, value, header_fmt)

    # Column Widths & Locking Strategy
    worksheet.set_column('A:H', 20, locked_text) # Meta data locked
    worksheet.set_column('I:I', 25, unlocked_input) # ASSESSMENT: UNLOCKED
    worksheet.set_column('J:K', 12, locked_calc)    # Scores locked
    worksheet.set_column('L:L', 35, unlocked_input) # NOTES: UNLOCKED

    # 7. Formulas and Dropdowns
    for i in range(len(df_main)):
        excel_row = i + 1
        
        # Dropdown
        valid_options = dropdown_map.get(i, [])
        if valid_options:
            worksheet.data_validation(excel_row, 8, excel_row, 8, {
                'validate': 'list', 'source': valid_options
            })
            guidance = guidance_map.get(i)
            if guidance:
                msg = "\n".join(f"{k}: {v.strip()}" for k, v in guidance.items())
                worksheet.write_comment(excel_row, 8, msg, {'title': 'Scale Guidance'})

        # Calculations
        cell_id = f"B{excel_row + 1}"
        cell_assess = f"I{excel_row + 1}"
        cell_weight = f"G{excel_row + 1}"
        
        # VLOOKUP for score
        worksheet.write_formula(excel_row, 9, f'=IFERROR(VLOOKUP({cell_id}&"_"&{cell_assess}, Score_Ref!A:B, 2, FALSE), 0)', locked_calc)
        # Weighted calculation
        worksheet.write_formula(excel_row, 10, f'=J{excel_row + 1}*{cell_weight}', locked_calc)

    # 8. Protection - Finally, enable it!
    # No password used here, but you can add one: worksheet.protect('password')
    worksheet.protect()

    # Total Score at bottom
    last_row = len(df_main) + 1
    worksheet.write(last_row, 9, "TOTAL:", header_fmt)
    worksheet.write_formula(last_row, 10, f"=SUM(K2:K{last_row})", header_fmt)

    writer.close()
    print(f"Secured Audit file created: {output_file}")

@click.command()
@click.argument("input", default=None, required=False, type=click.Path(exists=True))
@click.argument("output", default=None, required=False, type=click.Path())
def main(input, output):
    root = Path(__file__).parent.parent
    input = input or str(root / "gsp_level2.yml")
    output = output or str(root / "Green_Software_Audit_Secure.xlsx")
    convert_yaml_to_protected_excel(input, output)

if __name__ == "__main__":
    main()
