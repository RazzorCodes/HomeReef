import os
import re

def replace_in_content(content):
    # Rule 8: spacesaver-transcode -> homereef-transflux
    content = content.replace("spacesaver-transcode", "homereef-transflux")
    
    # Rule 10: sps-transcode-test -> reef-transflux-test
    content = content.replace("sps-transcode-test", "reef-transflux-test")
    
    # Rule 7: TRANSCODER_URL -> TRANSFLUX_URL
    content = content.replace("TRANSCODER_URL", "TRANSFLUX_URL")
    
    # Rule 1, 2, 3: SpaceSaver -> HomeReef
    content = content.replace("SpaceSaver", "HomeReef")
    content = content.replace("spacesaver", "homereef")
    content = content.replace("SPACESAVER", "HOMEREEF")
    
    # Rule 4, 5, 6: Spyglass -> Seaglass
    content = content.replace("Spyglass", "Seaglass")
    content = content.replace("spyglass", "seaglass")
    content = content.replace("SPYGLASS", "SEAGLASS")
    
    # Rule 9: transcoder -> transflux (case-insensitive, match original casing)
    # Since we are doing specific casing already, we can just do:
    content = content.replace("Transcoder", "Transflux")
    content = content.replace("transcoder", "transflux")
    content = content.replace("TRANSCODER", "TRANSFLUX")
    
    # Rule 10: sps -> reef (as abbreviation)
    # We should be careful. Usually "sps" is used in things like "sps-..."
    # Let's use word boundaries or look for it as a prefix in strings.
    # Looking at grep, it was "sps-transcode-test".
    # Are there other "sps"?
    # The user said: when it appears as an abbreviation in strings or filenames.
    content = re.sub(r'\bsps\b', 'reef', content)
    # Also handle things like sps-
    content = re.sub(r'sps-', 'reef-', content)
    
    return content

exclude_dirs = {'.git', '.venv', '__pycache__', '.ruff_cache', '.pytest_cache'}

for root, dirs, files in os.walk('.', topdown=True):
    dirs[:] = [d for d in dirs if d not in exclude_dirs]
    
    for name in files:
        if name == 'rename_script.py':
            continue
        file_path = os.path.join(root, name)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            new_content = replace_in_content(content)
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                print(f"Updated: {file_path}")
        except UnicodeDecodeError:
            # Skip binary files
            pass
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
