import sys
import os
import json
import re


def check_report_content(text, competitor, platform, ads_data):
    """
    Check report text for expected content about competitor and platform:
    - total ads count
    - top 3 messaging themes
    - example copy snippets
    """
    success_checks = []
    failures = []

    # Normalize text lowercase for case-insensitive search
    text_lower = text.lower()

    # Check total ads count
    expected_count = len(ads_data.get(competitor, {}).get(platform, []))

    count_patterns = [
        f"total number of ads", 
        f"{expected_count}", 
        competitor.lower(), 
        platform.lower()
    ]
    count_found = all(any(p in text_lower for p in [str(expected_count), f'{expected_count} ads', f'{expected_count} active ads'])
                      for p in [str(expected_count)])
    # Less strict: just check expected_count number appears near competitor and platform
    count_found = False
    pattern_num = re.compile(r'\b(\d+)\b')
    # We'll just check competitor and platform and digit appear in the same paragraph
    paras = re.split(r'\n\n+', text_lower)
    for p in paras:
        if competitor.lower() in p and platform.lower() in p:
            nums = [int(m) for m in pattern_num.findall(p)]
            if expected_count in nums:
                count_found = True
                break

    success_checks.append(('total ads count mention', count_found,
                           f'Total ads for {competitor} {platform} expected {expected_count}'))

    # Check top 3 themes mentioned in text
    # Get themes freq
    themes = [a.get('theme','').lower() for a in ads_data.get(competitor, {}).get(platform, [])]
    from collections import Counter
    theme_counts = Counter(themes)
    top3 = [t for t,_ in theme_counts.most_common(3)]

    theme_text_checks = [any(t in text_lower for t in top3)]
    theme_found = any(theme_text_checks)
    success_checks.append(('top 3 themes mentioned', theme_found,
                           f'Top themes: {top3}'))

    # Check at least one example copy snippet included
    copies = [a.get('copy','').lower() for a in ads_data.get(competitor, {}).get(platform, [])]
    copy_found = any(copy.lower() in text_lower for copy in copies if len(copy) > 10) # check for longer than 10 chars
    success_checks.append(('example copy snippets present', copy_found, 'At least 1 ad copy snippet must appear'))

    # Check presence of common markdown structures: headings, bullets or numbered list
    heading = bool(re.search(r'#{1,6}\s', text))
    bullets = bool(re.search(r'^\s*[-*+]\s', text, flags=re.MULTILINE))
    numbered = bool(re.search(r'^\s*\d+\.\s', text, flags=re.MULTILINE))
    md_structure = heading and (bullets or numbered)

    success_checks.append(('markdown structure usage', md_structure, 'Headings and bullets or numbered lists present'))

    passed = all(s[1] for s in success_checks)
    return passed, success_checks


def check_screenshots(ads_data, root_dir):
    # Verify all expected PNG files exist with proper folder structure
    # and that PNG files are nonempty.
    all_checks = []
    all_passed = True

    for competitor, platforms in ads_data.items():
        for platform, ads in platforms.items():
            dir_path = os.path.join(root_dir, 'competitor-ads', competitor.lower(), platform.lower())
            if not os.path.isdir(dir_path):
                all_checks.append({
                    'name': f'{competitor}-{platform} folder exists',
                    'passed': False,
                    'detail': f'Folder {dir_path} does not exist'
                })
                all_passed = False
                continue

            # All expected filenames
            expected_files = [f"{competitor.lower()}_{platform.lower()}_{ad.get('id','')}.png" for ad in ads]
            found_files = os.listdir(dir_path)

            missing = [f for f in expected_files if f not in found_files]

            if missing:
                all_checks.append({
                    'name': f'{competitor}-{platform} missing images',
                    'passed': False,
                    'detail': f'Missing {len(missing)} images: {missing}'
                })
                all_passed = False
            else:
                all_checks.append({
                    'name': f'{competitor}-{platform} all images present',
                    'passed': True,
                    'detail': f'All {len(expected_files)} images found'
                })

            # Check files are >0 bytes
            for fname in expected_files:
                file_path = os.path.join(dir_path, fname)
                size = 0
                try:
                    size = os.path.getsize(file_path)
                except Exception as e:
                    size = 0
                if size < 100:
                    all_checks.append({
                        'name': f'{competitor}-{platform} image {fname} nonempty',
                        'passed': False,
                        'detail': f'File size {size} too small'
                    })
                    all_passed = False

    return all_passed, all_checks


def main():
    if len(sys.argv) != 2:
        print(json.dumps({
            'passed': False,
            'score': 0.0,
            'checks': [{'name':'argument check','passed':False,'detail':'Expected one argument: workspace path'}]
        }))
        return

    workspace = sys.argv[1]

    # Load ads data metadata
    ads_metadata_path = os.path.join(workspace, 'competitor-ads', 'ads_metadata.json')
    if not os.path.isfile(ads_metadata_path):
        # fail early
        print(json.dumps({
            'passed': False,
            'score': 0.0,
            'checks': [{'name': 'ads metadata present','passed': False, 'detail': 'ads_metadata.json missing'}]
        }))
        return

    with open(ads_metadata_path, 'r') as f:
        ads_data = json.load(f)

    # Find the markdown report(s) named competitive_ads_analysis.md (exact)
    md_files = []
    for root, dirs, files in os.walk(workspace):
        for f in files:
            if f.lower() == 'competitive_ads_analysis.md':
                md_files.append(os.path.join(root, f))

    if not md_files:
        print(json.dumps({
            'passed': False,
            'score': 0.0,
            'checks': [{'name': 'markdown report file', 'passed': False, 'detail': 'No competitive_ads_analysis.md file found'}]
        }))
        return

    # Evaluate each markdown report; take best score
    best_score = 0.0
    best_checks = None

    for mdfile in md_files:
        with open(mdfile, 'r', encoding='utf-8') as f:
            text = f.read()
        # Aggregate all checks from competitors * platforms
        all_checks = []
        all_pass = True
        for competitor in ads_data.keys():
            for platform in ads_data[competitor].keys():
                passed, checks = check_report_content(text, competitor, platform, ads_data)
                all_checks.extend([{"name": f"{c[0]} ({competitor}-{platform})", "passed": c[1], "detail": c[2]} for c in checks])
                if not passed:
                    all_pass = False

        # Also check screenshots
        screenshots_passed, screenshots_checks = check_screenshots(ads_data, workspace)
        all_checks.extend(screenshots_checks)

        if not screenshots_passed:
            all_pass = False

        # Calculate score
        score = sum(1 for c in all_checks if c['passed']) / len(all_checks) if all_checks else 0.0

        if score > best_score:
            best_score = score
            best_checks = all_checks

    final_passed = best_score >= 0.8

    print(json.dumps({
        'passed': final_passed,
        'score': best_score,
        'checks': best_checks if best_checks else []
    }))


if __name__ == '__main__':
    main()
