"""XlinOS installer: everything that is not drawing. Choices, per-screen checks, texts and their translations, region / keyboard
lists, network helpers and the options handed to the install engine. The screen (xlinos-installer) only shows this.
The engine (xlinos-install-run) re-checks every disk rule itself; nothing here is trusted by it."""
import json, os, re, subprocess

SHARE = os.environ.get("XLINOS_SHARE", "/usr/share/xlinos")
LIB = os.path.dirname(os.path.abspath(__file__))

# ------------------------------------------------------------------ languages and texts
LANGS = [("English (United States)", "en_US.UTF-8"), ("English (United Kingdom)", "en_GB.UTF-8"), ("हिन्दी (Hindi)", "hi_IN.UTF-8"),
         ("Deutsch (German)", "de_DE.UTF-8"), ("Français (French)", "fr_FR.UTF-8"), ("Español (Spanish)", "es_ES.UTF-8"),
         ("Português (Brasil)", "pt_BR.UTF-8"), ("Italiano", "it_IT.UTF-8"), ("Русский (Russian)", "ru_RU.UTF-8"),
         ("Japanese", "ja_JP.UTF-8"), ("Chinese (Simplified)", "zh_CN.UTF-8"), ("العربية (Arabic)", "ar_SA.UTF-8")]
TRANSLATED = ("en", "hi", "de", "fr", "es")      # installer texts exist in these; every other language shows English text

# key: (en, hi, de, fr, es)
_T = {
 "welcome": ("Welcome to XlinOS", "XlinOS में आपका स्वागत है", "Willkommen bei XlinOS", "Bienvenue dans XlinOS", "Bienvenido a XlinOS"),
 "welcome_msg": ("A clean, fast and lightweight operating system. This setup takes a few minutes and has five short steps.",
                 "एक साफ़, तेज़ और हल्का ऑपरेटिंग सिस्टम। इस सेटअप में कुछ मिनट लगते हैं और पाँच छोटे चरण हैं।",
                 "Ein sauberes, schnelles und leichtes Betriebssystem. Die Einrichtung dauert wenige Minuten und hat fünf kurze Schritte.",
                 "Un système propre, rapide et léger. L'installation prend quelques minutes et comporte cinq courtes étapes.",
                 "Un sistema limpio, rápido y ligero. La instalación lleva unos minutos y tiene cinco pasos cortos."),
 "choose_lang": ("Choose your language", "अपनी भाषा चुनें", "Sprache wählen", "Choisissez votre langue", "Elige tu idioma"),
 "continue": ("Continue", "आगे बढ़ें", "Weiter", "Continuer", "Continuar"),
 "back": ("Back", "पीछे", "Zurück", "Retour", "Atrás"),
 "edit": ("Edit", "बदलें", "Ändern", "Modifier", "Cambiar"),
 "install": ("Install", "इंस्टॉल करें", "Installieren", "Installer", "Instalar"),
 "cancel": ("Cancel", "रद्द करें", "Abbrechen", "Annuler", "Cancelar"),
 "restart": ("Restart", "पुनः आरंभ करें", "Neu starten", "Redémarrer", "Reiniciar"),
 "about_title": ("About, agreement and privacy", "परिचय, सहमति और गोपनीयता", "Info, Vereinbarung und Datenschutz", "À propos, accord et confidentialité", "Acerca de, acuerdo y privacidad"),
 "sec_about": ("About XlinOS", "XlinOS के बारे में", "Über XlinOS", "À propos de XlinOS", "Acerca de XlinOS"),
 "sec_agree": ("Installation agreement", "इंस्टॉलेशन समझौता", "Installationsvereinbarung", "Accord d'installation", "Acuerdo de instalación"),
 "sec_privacy": ("Privacy and diagnostics", "गोपनीयता और डायग्नोस्टिक्स", "Datenschutz und Diagnose", "Confidentialité et diagnostics", "Privacidad y diagnóstico"),
 "accept": ("I have read and accept the installation agreement (required)", "मैंने इंस्टॉलेशन समझौता पढ़ लिया है और स्वीकार करता/करती हूँ (आवश्यक)",
            "Ich habe die Installationsvereinbarung gelesen und akzeptiere sie (erforderlich)", "J'ai lu et j'accepte l'accord d'installation (obligatoire)", "He leído y acepto el acuerdo de instalación (obligatorio)"),
 "diag_opt": ("Keep a copy of the installation log on the new system, to help find problems (optional, off by default)",
              "समस्याएँ ढूँढने में मदद के लिए इंस्टॉलेशन लॉग की एक प्रति नए सिस्टम पर रखें (वैकल्पिक, डिफ़ॉल्ट रूप से बंद)",
              "Eine Kopie des Installationsprotokolls auf dem neuen System behalten, um Probleme zu finden (optional, standardmäßig aus)",
              "Garder une copie du journal d'installation sur le nouveau système pour trouver des problèmes (facultatif, désactivé par défaut)",
              "Guardar una copia del registro de instalación en el nuevo sistema para detectar problemas (opcional, desactivado por defecto)"),
 "legal_en": ("Legal texts are shown in English.", "कानूनी पाठ अंग्रेज़ी में दिखाए गए हैं।", "Rechtstexte werden auf Englisch angezeigt.", "Les textes juridiques sont affichés en anglais.", "Los textos legales se muestran en inglés."),
 "region_title": ("Language, region and keyboard", "भाषा, क्षेत्र और कीबोर्ड", "Sprache, Region und Tastatur", "Langue, région et clavier", "Idioma, región y teclado"),
 "language": ("Display language", "प्रदर्शन भाषा", "Anzeigesprache", "Langue d'affichage", "Idioma de la pantalla"),
 "country": ("Country or region", "देश या क्षेत्र", "Land oder Region", "Pays ou région", "País o región"),
 "timezone": ("Time zone", "समय क्षेत्र", "Zeitzone", "Fuseau horaire", "Zona horaria"),
 "kb_layout": ("Keyboard layout", "कीबोर्ड लेआउट", "Tastaturlayout", "Disposition du clavier", "Distribución del teclado"),
 "kb_variant": ("Keyboard variant", "कीबोर्ड वेरिएंट", "Tastaturvariante", "Variante du clavier", "Variante del teclado"),
 "kb_test": ("Type here to test your keyboard", "अपना कीबोर्ड जाँचने के लिए यहाँ टाइप करें", "Zum Testen der Tastatur hier tippen", "Tapez ici pour tester votre clavier", "Escribe aquí para probar tu teclado"),
 "default_variant": ("Default", "डिफ़ॉल्ट", "Standard", "Par défaut", "Predeterminada"),
 "disk_title": ("Internet, disk and installation method", "इंटरनेट, डिस्क और इंस्टॉलेशन विधि", "Internet, Datenträger und Installationsart", "Internet, disque et méthode d'installation", "Internet, disco y método de instalación"),
 "sec_net": ("Internet connection", "इंटरनेट कनेक्शन", "Internetverbindung", "Connexion Internet", "Conexión a Internet"),
 "sec_disk": ("Disks", "डिस्क", "Datenträger", "Disques", "Discos"),
 "sec_method": ("Installation method", "इंस्टॉलेशन विधि", "Installationsart", "Méthode d'installation", "Método de instalación"),
 "review_title": ("Review and confirm", "समीक्षा और पुष्टि", "Prüfen und bestätigen", "Vérifier et confirmer", "Revisar y confirmar"),
 "thanks": ("Thanks for Choosing XlinOS", "XlinOS चुनने के लिए धन्यवाद", "Danke, dass Sie XlinOS gewählt haben", "Merci d'avoir choisi XlinOS", "Gracias por elegir XlinOS"),
 "thanks_msg": ("We are installing XlinOS on your computer. Please keep it plugged in.", "हम आपके कंप्यूटर पर XlinOS इंस्टॉल कर रहे हैं। कृपया इसे चालू रखें।",
                "XlinOS wird auf Ihrem Computer installiert. Bitte lassen Sie ihn eingeschaltet.", "XlinOS est en cours d'installation. Veuillez laisser l'ordinateur allumé.", "Estamos instalando XlinOS en tu equipo. Mantenlo encendido."),
 "ready": ("XlinOS is Ready!", "XlinOS तैयार है!", "XlinOS ist bereit!", "XlinOS est prêt !", "¡XlinOS está listo!"),
 "ready_msg": ("XlinOS has been successfully installed.", "XlinOS सफलतापूर्वक इंस्टॉल हो गया है।", "XlinOS wurde erfolgreich installiert.", "XlinOS a été installé avec succès.", "XlinOS se ha instalado correctamente."),
 "show_log": ("Show details", "विवरण दिखाएँ", "Details anzeigen", "Afficher les détails", "Mostrar detalles"),
 "loading": ("Starting the installer", "इंस्टॉलर शुरू हो रहा है", "Installationsprogramm startet", "Démarrage de l'installateur", "Iniciando el instalador"),
}
_IDX = {c: i for i, c in enumerate(TRANSLATED)}

def lang_code(locale):
    return (locale or "en_US").split("_")[0].split(".")[0]

def tr(locale, key):
    row = _T.get(key)
    if not row: return key
    return row[_IDX.get(lang_code(locale), 0)] or row[0]

# ------------------------------------------------------------------ texts: about, agreement, privacy (taken from the repository, nothing invented)
def read_version():
    for p in (os.path.join(SHARE, "VERSION"), "/etc/xlinos-release", os.path.join(LIB, "../../../../../../VERSION")):
        try:
            v = open(p).read().strip().splitlines()[0]
            if v: return v.replace("VERSION=", "").strip('"')
        except Exception: pass
    return "0.1.0"

ABOUT = ("XlinOS is a clean, professional and lightweight operating system that aims to be fast, smooth and useful on any device. "
         "It brings its own desktop, apps and settings: a status bar on top, a run bar for your apps, a launcher, Files, Settings, a terminal called Quickshell and more. "
         "XlinOS is made by Madhav Sharma and presented by Axion Co.")

def license_text():
    for p in (os.path.join(SHARE, "LICENSE"), "/usr/share/licenses/xlinos/LICENSE", os.path.join(LIB, "../../../../../../LICENSE")):
        try: return open(p).read().strip()
        except Exception: pass
    return "The licence text could not be loaded from the installation medium."

AGREEMENT_DRAFT = ("DRAFT INSTALLATION TERMS: placeholder for review, not legal advice and not legally approved.\n\n"
    "1. XlinOS is installed on this computer at your request. You choose the disk and the installation method.\n"
    "2. Installing can erase or change data on the disk you choose. Make a backup of anything you want to keep before you continue.\n"
    "3. XlinOS is provided as is, without warranty, under the licence shown below. Software it brings along (the Linux kernel, drivers and other programs) "
    "has its own licences, which are installed with it.\n"
    "4. Final installation terms will replace this draft before XlinOS is released.")

PRIVACY = ("The installer itself collects no personal data and sends nothing about you or your computer to anyone. There is no analytics or tracking in the installer.\n\n"
    "While installing, your computer downloads the system packages over the internet. The servers you download from can see the normal connection details "
    "(your network address and which packages you fetch), as with any download.\n\n"
    "Your choices (language, region, time zone, keyboard) are kept on your computer only. No account is created here: you create your user on the first start.\n\n"
    "Optional, off by default: keep a copy of the installation log on the new system so you can look at it later. It stays on your computer and is not sent anywhere.")

# ------------------------------------------------------------------ regions, time zones, keyboards
def countries():
    out = []
    try:
        for l in open("/usr/share/zoneinfo/iso3166.tab"):
            if l.startswith("#") or "\t" not in l: continue
            code, name = l.rstrip("\n").split("\t", 1); out.append((name, code))
    except Exception:
        out = [("United States", "US"), ("India", "IN"), ("United Kingdom", "GB"), ("Germany", "DE"), ("France", "FR"), ("Spain", "ES")]
    return sorted(out)

PREFERRED_ZONE = {"US": "America/New_York", "IN": "Asia/Kolkata", "GB": "Europe/London", "DE": "Europe/Berlin", "FR": "Europe/Paris", "ES": "Europe/Madrid",
                  "BR": "America/Sao_Paulo", "RU": "Europe/Moscow", "CN": "Asia/Shanghai", "JP": "Asia/Tokyo", "CA": "America/Toronto", "AU": "Australia/Sydney",
                  "IT": "Europe/Rome", "SA": "Asia/Riyadh", "MX": "America/Mexico_City"}

def zones_for(code):
    zs = []
    try:
        for l in open("/usr/share/zoneinfo/zone1970.tab"):
            if l.startswith("#"): continue
            f = l.rstrip("\n").split("\t")
            if len(f) > 2 and code in f[0].split(","): zs.append(f[2])
    except Exception: pass
    if not zs:
        try:
            for l in open("/usr/share/zoneinfo/zone.tab"):
                if l.startswith("#"): continue
                f = l.rstrip("\n").split("\t")
                if len(f) > 2 and f[0] == code: zs.append(f[2])
        except Exception: pass
    zs = sorted(set(zs)) or ["UTC"]
    pz = PREFERRED_ZONE.get(code)
    return ([pz] + [z for z in zs if z != pz]) if pz in zs else zs

def all_zones():
    out = set()
    try:
        for l in open("/usr/share/zoneinfo/zone1970.tab"):
            if not l.startswith("#"): out.add(l.split("\t")[2].strip())
    except Exception: out = {"UTC"}
    return sorted(out) or ["UTC"]

def default_region(locale):
    """Suggestion only, from the language's country (en_GB -> GB); the person can change it."""
    m = re.match(r"[a-z]+_([A-Z]{2})", locale or "")
    return m.group(1) if m else "US"

KB_FALLBACK = [("English (US)", "us"), ("English (UK)", "gb"), ("Hindi (Bolnagri)", "in"), ("German", "de"), ("French", "fr"), ("Spanish", "es"),
               ("Portuguese (Brazil)", "br"), ("Italian", "it"), ("Russian", "ru"), ("Japanese", "jp"), ("Arabic", "ara")]

def keyboards():
    """({layout code: name}, {layout code: [(variant code, name)]}) from the keyboard database."""
    lay, var, sec = {}, {}, None
    try:
        for l in open("/usr/share/X11/xkb/rules/base.lst", encoding="utf-8", errors="replace"):
            l = l.rstrip("\n")
            if l.startswith("! "): sec = l[2:].strip(); continue
            if not l.strip(): continue
            if sec == "layout":
                a = l.split(None, 1)
                if len(a) == 2: lay[a[0]] = a[1].strip()
            elif sec == "variant":
                m = re.match(r"\s+(\S+)\s+(\S+): (.*)", l)
                if m: var.setdefault(m.group(2), []).append((m.group(1), m.group(3).strip()))
    except Exception: pass
    if not lay: lay = {c: n for n, c in KB_FALLBACK}
    return lay, var

def default_keyboard(locale, lay):
    m = re.match(r"[a-z]+_([A-Z]{2})", locale or "")
    cc = m.group(1).lower() if m else "us"
    cc = {"gb": "gb", "in": "in", "br": "br", "jp": "jp", "sa": "ara"}.get(cc, cc)
    return cc if cc in lay else ("us" if "us" in lay else next(iter(lay)))

# ------------------------------------------------------------------ choices
class Choices:
    def __init__(self):
        self.locale = "en_US.UTF-8"
        self.country = "US"; self.tz = "America/New_York"
        self.kb = "us"; self.kb_variant = ""
        self.agreed = False; self.diag_log = False
        self.disks = []              # last disk scan
        self.method = ""             # erase | freespace | partition
        self.disk = ""               # disk (erase, freespace) or the partition to use (partition)
        self.efi = ""
        self.fs = "ext4"
        self.hostname = "xlin"
        self.confirmed_loss = False
        self.net = {"state": "unknown", "text": ""}

def method_label(m):
    return {"erase": "Erase the disk and install XlinOS", "freespace": "Install alongside other systems, in free space",
            "partition": "Use a partition you choose (advanced)"}.get(m, "Not chosen")

def disk_by_path(c, path):
    for d in c.disks:
        if d["path"] == path: return d
        for p in d["partitions"]:
            if p["path"] == path: return d
    return None

def target_disk(c):
    return disk_by_path(c, c.disk)

def destructive(c):
    return c.method in ("erase", "partition", "freespace")

def losses(c):
    """What the install will erase or change, in plain words (shown on Review and in the final confirmation)."""
    d = target_disk(c)
    if not d: return ""
    name = "%s (%s)" % (d["model"], d["path"])
    if c.method == "erase": return "EVERYTHING on %s will be erased, including every system and file on it." % name
    if c.method == "partition": return "Everything on the partition %s will be erased. Other partitions and the other systems stay; XlinOS adds itself to the shared start-up partition %s." % (c.disk, c.efi)
    if c.method == "freespace": return "A new partition is created in the free space on %s. Existing partitions are not changed; XlinOS adds itself to the shared start-up partition %s." % (name, c.efi)
    return ""

def check_step(step, c):
    """Problems that stop the person from leaving a screen, as plain sentences (empty = fine). Step numbers: 1 welcome ... 5 review."""
    e = []
    if step == 2 and not c.agreed: e.append("Please accept the installation agreement to continue.")
    if step == 3:
        if not c.country: e.append("Choose your country or region.")
        if c.tz not in all_zones() and c.tz != "UTC": e.append("Choose a valid time zone.")
        lay, var = keyboards()
        if c.kb not in lay: e.append("Choose a keyboard layout.")
        elif c.kb_variant and c.kb_variant not in [v for v, _ in var.get(c.kb, [])]: e.append("That keyboard variant does not belong to this layout.")
    if step == 4:
        if not c.method: e.append("Choose how to install XlinOS.")
        d = target_disk(c)
        if c.method and not d: e.append("Choose the disk or partition to use.")
        if d:
            if d.get("protected"): e.append("%s cannot be used: %s." % (d["path"], d["protected"]))
            if d.get("readonly"): e.append("%s is read only." % d["path"])
            if c.method in ("partition", "freespace") and not c.efi: e.append("Choose the existing start-up (EFI) partition to share.")
    if step == 5:
        if destructive(c) and not c.confirmed_loss: e.append("Tick the box to confirm that you understand what will be changed.")
    return e

def review(c):
    """[(label, value, step to edit it on)] for the Review screen. No secrets exist in this installer."""
    d = target_disk(c)
    lay, var = keyboards()
    cn = dict((code, n) for n, code in countries()).get(c.country, c.country)
    lname = next((n for n, v in LANGS if v == c.locale), c.locale)
    kb = lay.get(c.kb, c.kb) + ((" - " + dict(var.get(c.kb, [])).get(c.kb_variant, c.kb_variant)) if c.kb_variant else "")
    rows = [("Language", lname, 3), ("Region", cn, 3), ("Time zone", c.tz, 3), ("Keyboard", kb, 3),
            ("Internet", c.net.get("text") or "Not connected (the system is downloaded while installing)", 4),
            ("Installation method", method_label(c.method), 4)]
    if d:
        rows.append(("Disk", "%s  %s  (%s)" % (d["model"], human(d["size"]), d["path"]), 4))
        if c.method == "partition": rows.append(("Partition to erase", c.disk, 4))
        if c.method in ("partition", "freespace"): rows.append(("Shared start-up partition", c.efi, 4))
        if c.method == "freespace": rows.append(("New partition", "created in free space (%s available)" % human(d.get("biggest_gap", 0)), 4))
        if c.method == "erase": rows.append(("Partitions", "Start-up partition 512 MB + system partition (rest of the disk), %s" % c.fs, 4))
        others = [("%s: %s" % (p["path"], p["os"])) for p in d["partitions"] if p.get("os")]
        rows.append(("Other systems found", "; ".join(others) if others else "None detected", 4))
    rows.append(("Installation log copy", "Yes, kept on the new system" if c.diag_log else "No", 2))
    return rows

def human(n):
    n = int(n or 0)
    return "%.0f GB" % (n / 1e9) if n >= 1e9 else "%.0f MB" % (n / 1e6)

def engine_options(c):
    return {"target": {"erase": "disk", "freespace": "freespace", "partition": "partition"}[c.method], "efi": c.efi, "locale": c.locale, "kb": c.kb,
            "kb_variant": c.kb_variant, "tz": c.tz, "fs": c.fs, "hostname": c.hostname, "diag_log": bool(c.diag_log)}

def media_kind(c):
    """How the installer was started, for the last screen: usb | file | other."""
    for d in c.disks:
        r = d.get("protected") or ""
        if "file on this disk" in r: return "file"
        if r and (d.get("tran") == "usb" or d.get("removable")): return "usb"
    return "other"

# ------------------------------------------------------------------ disks
def scan_disks(fast=False):
    cmd = ["python3", os.path.join(LIB, "xlinos_disks.py"), "scan"] + (["--fast"] if fast else [])
    if os.geteuid() != 0: cmd = ["sudo", "-n"] + cmd
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
        return json.loads(r.stdout)
    except Exception:
        return None     # could not be read (not the same as "no disks")

def disk_flags(d):
    f = []
    if d.get("protected"): f.append("Installation medium")
    if d.get("readonly"): f.append("Read only")
    if d.get("busy"): f.append("In use")
    if d.get("removable") or d.get("tran") == "usb": f.append("Removable")
    return f

def methods_for(d, c_efi_boot=True):
    """Which installation methods this disk allows, with the reason when one does not: {method: (allowed, why)}."""
    esp = [p for p in d["partitions"] if p.get("esp")]
    free = [p for p in d["partitions"] if not p.get("esp") and not p.get("mounted") and p["size"] >= 10 * 10**9]
    blocked = d.get("protected") or ("Read only" if d.get("readonly") else "")
    r = {}
    r["erase"] = (not blocked and d["size"] >= 16 * 10**9, blocked or ("Too small (16 GB needed)" if d["size"] < 16 * 10**9 else ""))
    why = blocked or ("Needs a GPT disk with an existing start-up (EFI) partition" if d.get("table") != "gpt" or not esp else
                      ("No free space of 10 GB or more. Free some up first (for example shrink a partition from your other system)" if d.get("biggest_gap", 0) < 10 * 10**9 else ""))
    r["freespace"] = (not why, why)
    why = blocked or ("Needs an existing start-up (EFI) partition" if not esp else ("No unused partition of 10 GB or more" if not free else ""))
    r["partition"] = (not why, why)
    return r

def free_partitions(d):
    return [p for p in d["partitions"] if not p.get("esp") and not p.get("mounted") and p["size"] >= 10 * 10**9]

# ------------------------------------------------------------------ network (NetworkManager)
def _nm(*a, timeout=25):
    cmd = ["nmcli"] + list(a)
    try:
        return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    except Exception as e:
        return subprocess.CompletedProcess(cmd, 127, "", str(e))

def net_status():
    """{'state': connected|disconnected|unavailable, 'ethernet': text, 'wifi': text, 'text': one line, 'wifi_present': bool}"""
    r = _nm("-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "device")
    if r.returncode != 0:
        return {"state": "unavailable", "ethernet": "", "wifi": "", "text": "Network manager is not available", "wifi_present": False}
    eth = wifi = ""; present = False; conn = False; text = []
    for l in r.stdout.splitlines():
        f = l.split(":")
        if len(f) < 4: continue
        dev, typ, st, con = f[0], f[1], f[2], f[3]
        if typ == "ethernet":
            eth = "Cable: connected (%s)" % dev if st == "connected" else "Cable: %s" % ("not plugged in" if st in ("unavailable", "disconnected") else st)
            if st == "connected": conn = True; text.append("Cable")
        elif typ == "wifi":
            present = True
            wifi = "Wi-Fi: connected to %s" % con if st == "connected" else "Wi-Fi: %s" % ("not connected" if st in ("disconnected", "connecting (getting IP configuration)") else st)
            if st == "connected": conn = True; text.append("Wi-Fi " + con)
    if not eth and not wifi: return {"state": "unavailable", "ethernet": "", "wifi": "", "text": "No network adapter found. You can install without internet only if the system files are available offline (they are not yet), so connect a cable or Wi-Fi.", "wifi_present": False}
    on = _nm("-t", "-f", "CONNECTIVITY", "general").stdout.strip()
    return {"state": "connected" if conn else "disconnected", "ethernet": eth, "wifi": wifi, "wifi_present": present,
            "text": ("Connected: " + ", ".join(text) + (" (no internet reply yet)" if on not in ("full", "") and on != "full" else "")) if conn else "Not connected"}

def wifi_list(rescan=True):
    r = _nm("-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "yes" if rescan else "no", timeout=40)
    out, seen = [], set()
    for l in r.stdout.splitlines():
        f = re.split(r"(?<!\\):", l)
        if len(f) < 4 or not f[1].strip(): continue
        ssid = f[1].replace("\\:", ":")
        if ssid in seen: continue
        seen.add(ssid)
        out.append({"ssid": ssid, "signal": int(f[2] or 0), "secure": bool(f[3].strip() and f[3].strip() != "--"), "active": f[0].strip() == "*"})
    return sorted(out, key=lambda w: (not w["active"], -w["signal"]))

def wifi_connect(ssid, password=""):
    """(ok, message). The password goes straight to NetworkManager and is never stored by the installer."""
    cmd = ["device", "wifi", "connect", ssid] + (["password", password] if password else [])
    r = _nm(*cmd, timeout=60)
    if r.returncode == 0: return True, "Connected to %s" % ssid
    msg = (r.stderr or r.stdout).strip()
    if "Secrets were required" in msg or "password" in msg.lower(): msg = "The password was not accepted."
    elif "No network with SSID" in msg: msg = "That network is no longer in range."
    return False, msg or "Could not connect."

def disconnect_wifi():
    r = _nm("-t", "-f", "DEVICE,TYPE,STATE", "device")
    for l in r.stdout.splitlines():
        f = l.split(":")
        if len(f) >= 3 and f[1] == "wifi" and f[2] == "connected": return _nm("device", "disconnect", f[0]).returncode == 0
    return False

# ------------------------------------------------------------------ keyboard preview (applies to the running installer session)
def apply_keyboard(layout, variant=""):
    cmd = ["xlinctl", "layout", re.sub(r"[^a-z0-9_]", "", layout)]
    if variant: cmd.append(re.sub(r"[^a-zA-Z0-9_-]", "", variant))
    try: return subprocess.run(cmd, capture_output=True, timeout=5).returncode == 0
    except Exception: return False
