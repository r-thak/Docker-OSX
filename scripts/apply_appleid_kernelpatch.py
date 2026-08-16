#!/usr/bin/env python3
import plistlib
import base64
import os
import shutil
import sys

def add_kernel_patches(config_path):
    # Make a backup of the original file
    backup_path = config_path + '.backup'
    shutil.copy2(config_path, backup_path)
    print(f"Backup created at {backup_path}")

    # Read the plist file
    try:
        with open(config_path, 'rb') as f:
            config = plistlib.load(f)
    except (plistlib.InvalidFileException, ValueError, OSError) as e:
        print(f"Error: Failed to parse {config_path} as a plist: {e}")
        print(f"Your original file was not modified; a backup is available at {backup_path}")
        return False

    # Prepare the patch entries
    patch1 = {
        'Arch': 'x86_64',
        'Base': '',
        'Comment': 'Sonoma VM BT Enabler - PART 1 of 2 - Patch kern.hv_vmm_present=0',
        'Count': 1,
        'Enabled': True,
        'Find': base64.b64decode('aGliZXJuYXRlaGlkcmVhZHkAaGliZXJuYXRlY291bnQA'),
        'Identifier': 'kernel',
        'Limit': 0,
        'Mask': b'',
        'MaxKernel': '',
        'MinKernel': '20.4.0',
        'Replace': base64.b64decode('aGliZXJuYXRlaGlkcmVhZHkAaHZfdm1tX3ByZXNlbnQA'),
        'ReplaceMask': b'',
        'Skip': 0,
    }

    patch2 = {
        'Arch': 'x86_64',
        'Base': '',
        'Comment': 'Sonoma VM BT Enabler - PART 2 of 2 - Patch kern.hv_vmm_present=0',
        'Count': 1,
        'Enabled': True,
        'Find': base64.b64decode('Ym9vdCBzZXNzaW9uIFVVSUQAaHZfdm1tX3ByZXNlbnQA'),
        'Identifier': 'kernel',
        'Limit': 0,
        'Mask': b'',
        'MaxKernel': '',
        'MinKernel': '22.0.0',
        'Replace': base64.b64decode('Ym9vdCBzZXNzaW9uIFVVSUQAaGliZXJuYXRlY291bnQA'),
        'ReplaceMask': b'',
        'Skip': 0,
    }

    if 'Kernel' not in config or 'Patch' not in config['Kernel']:
        print("Error: Could not find Kernel -> Patch section in config.plist")
        return False

    # Figure out which of the two patches (if any) are already present.
    # Matching on the full comment (not just a shared substring) so that a
    # config with only PART 1 applied is correctly treated as half-patched
    # rather than being skipped as "already done".
    existing_comments = {
        patch['Comment']
        for patch in config['Kernel']['Patch']
        if isinstance(patch, dict) and 'Comment' in patch
    }
    missing = [p for p in (patch1, patch2) if p['Comment'] not in existing_comments]

    if not missing:
        print("Both Sonoma VM BT Enabler patches are already present; nothing to do.")
        return True

    if len(missing) == 1:
        present = patch1 if missing[0] is patch2 else patch2
        print(f"Warning: found '{present['Comment']}' but not its counterpart. "
              f"Config was only half-patched; adding the missing patch.")

    config['Kernel']['Patch'].extend(missing)

    # Write the updated plist file
    with open(config_path, 'wb') as f:
        plistlib.dump(config, f)

    print(f"Added {len(missing)} patch(es) to {config_path}")
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python apply_appleid_kernelpatch.py /path/to/config.plist")
        sys.exit(1)

    config_path = sys.argv[1]
    if not os.path.exists(config_path):
        print(f"Error: File {config_path} does not exist")
        sys.exit(1)

    success = add_kernel_patches(config_path)
    if success:
        print("Patches applied successfully. Please reboot to apply changes.")
    else:
        print("Failed to apply patches.")
        sys.exit(1)
