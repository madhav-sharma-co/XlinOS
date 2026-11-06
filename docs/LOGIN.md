# Login and users (Layer 5)

## What the user sees
1. **First start after install:** "Welcome to XlinOS. Create a user to start using". Full name, user name, password. The new user is logged in straight away.
2. **Every start:** XlinOS boot logo (Plymouth, planned), then a lock-style screen for the last user: clock, name, password, "Switch user".
3. **Switch user:** the list of users, plus "Create new user" and "Delete user".
4. **Inside the desktop:** logging out of Hyprland ends that user's session and returns to this screen.

## Rules (CEO decisions, 2026-11-05)
- The first user is created without a password check and is an administrator.
- New users after that need an administrator's password; they are standard users unless the box "Make this user an administrator" is ticked.
- Deleting a user needs that user's own password or an administrator's. The last administrator and logged-in users cannot be deleted. The files are kept unless "Also delete this user's files" is ticked (default: keep).

## How it works
| Part | File | Runs as |
|---|---|---|
| Login manager | `greetd` + `usr/share/xlinos/greetd-config.toml` | root |
| Login screen (GTK4, runs in `cage`) | `usr/local/lib/xlinos/xlinos-greeter` | user `greeter` (no rights) |
| Protocol and account client | `usr/local/lib/xlinos/xlinos_login.py` | same |
| Account helper (create, list, delete) | `usr/local/lib/xlinos/xlinos-accounts` | root, via one sudo rule for `greeter` (`usr/share/xlinos/sudoers-greeter`) |
| Session starter | `usr/local/bin/xlinos-session` | the user |

The screen never gets root rights. It can only call the helper, and the helper checks every rule itself.

## First login of each user
Xlin-soft's programs, packages and services are installed once for everyone during the install (`post-install.sh`). Each user's first login then only sets up their own settings, so standard users (no sudo) work too.

## Tested
- Account helper: 17 checks with real `useradd`/`userdel` in a private copy of `/etc` (CI "Tests").
- Login logic against a fake greetd, and every screen action with GTK stubbed (CI "Tests").
- The real screens drawn with real GTK (CI "UI preview", branch `ci-ui-preview`).
- **The whole flow on a real boot** (CI "Install test", branch `ci-shots-install`): an installed-style system (same package list and `post-install.sh` as the installer) boots to the first-start screen, the first user is created by typing into the form, the Xlin-soft desktop starts, after a restart the lock-style login shows, a wrong password gives "Wrong password.", and the right one logs in. All worked in QEMU (software graphics).
- **Not tested:** archinstall itself (disk menus), real hardware and GPU drivers, user switching/creating/deleting on the real screen (only on the stubbed one).

## Installing without archinstall's user step
In the archinstall menu, skip "User account" so the first-start screen creates the user. Calamares (later) will drop that step.
