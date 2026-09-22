# AgedProfiles Stock Alert

"Aged YouTube Accounts 2006 - 2009 with Videos" ka stock har 1 minute check hota hai.
Jab stock aaye (ya barhe) to Discord / WhatsApp pe message aata hai, kitne accounts aaye hain aur link ke saath.
Ye GitHub Actions pe chalta hai, is liye laptop band ho tab bhi kaam karta rehta hai.

## Setup (ek dafa)

1. **Discord webhook:** apne Discord server mein channel → Edit Channel → Integrations → Webhooks → New Webhook → **Copy Webhook URL**.
2. **WhatsApp (optional):** apne phone se **+34 644 71 81 99** ko WhatsApp pe ye bhejein:
   `I allow callmebot to send me messages` — jawab mein API key aayegi.
3. GitHub repo → **Settings → Secrets and variables → Actions → New repository secret**:
   - `DISCORD_WEBHOOK` = webhook URL
   - `WHATSAPP_PHONE` = apna number, jaise `+923001234567` (optional)
   - `WHATSAPP_APIKEY` = CallMeBot key (optional)
4. **Actions** tab → "Stock Monitor" → **Run workflow** → "Send a test message only" tick karein → test message aana chahiye.
   Phir ek dafa bina tick ke **Run workflow** dabayein; uske baad ye khud har waqt chalta rahega.

## Band karna / dobara chalana

- **Band:** Actions → Stock Monitor → `...` menu → **Disable workflow**. (Jo run chal raha ho usay **Cancel run** kar dein.)
- **Dobara chalu:** wahin **Enable workflow**.

## Aur products add karna

`monitor.py` mein `PRODUCTS` list mein naam aur link add kar dein.
