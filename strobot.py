import discord
import json
import os
from datetime import datetime

TOKEN = os.getenv("TOKEN")

KANAL_NAVN = "🪙-cryptopris"
ROLLE_NAVN = "Crypto"

intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

FIL = "strompris.json"

PRISER = {
    "svært lav": "🟢 Svært lav",
    "lav": "🟢 Lav",
    "normal": "🟡 Normal",
    "høy": "🟠 Høy",
    "svært høy": "🔴 Svært høy"
}


def hent_data():
    if not os.path.exists(FIL):
        return {}

    with open(FIL, "r", encoding="utf-8") as f:
        return json.load(f)


def lagre_data(data):
    with open(FIL, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class PrisView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        label="⚡ Oppdater strømpris",
        style=discord.ButtonStyle.primary,
        custom_id="oppdater_strompris"
    )
    async def oppdater(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):
        await interaction.response.send_message(
            "Velg den nye strømprisen:",
            view=Prisvalg(),
            ephemeral=True
        )


class Prisvalg(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=60)

        for navn in PRISER:
            self.add_item(PrisKnapp(navn))


class PrisKnapp(discord.ui.Button):
    def __init__(self, pris):
        super().__init__(
            label=PRISER[pris],
            style=discord.ButtonStyle.secondary
        )
        self.pris = pris

    async def callback(self, interaction: discord.Interaction):

        data = hent_data()

        gammel_pris = data.get("pris")
        ny_pris = self.pris

        data["pris"] = ny_pris
        data["sist_oppdatert"] = datetime.now().strftime("%d.%m.%Y %H:%M")
        data["melding_id"] = data.get("melding_id")

        lagre_data(data)

        kanal = interaction.channel

        # Oppdater den faste meldingen
        if data.get("melding_id"):
            try:
                melding = await kanal.fetch_message(
                    int(data["melding_id"])
                )

                await melding.edit(
                    content=(
                        "⚡ **STRØMPRIS**\n\n"
                        f"**{PRISER[ny_pris]}**\n\n"
                        f"Sist oppdatert: "
                        f"{data['sist_oppdatert']}\n\n"
                        "Trykk på knappen under for å oppdatere."
                    ),
                    view=PrisView()
                )

            except discord.NotFound:
                pass

        await interaction.response.edit_message(
            content=f"⚡ Strømprisen er oppdatert til **{PRISER[ny_pris]}**.",
            view=None
        )

        # Bare tagg hvis prisen faktisk har endret seg
        if gammel_pris != ny_pris:

            rolle = discord.utils.get(
                interaction.guild.roles,
                name=ROLLE_NAVN
            )

            if rolle:
                await kanal.send(
                    f"{rolle.mention} ⚡ **Strømprisen har endret seg!**\n"
                    f"Ny pris: **{PRISER[ny_pris]}**",
                    allowed_mentions=discord.AllowedMentions(
                        roles=True
                    )
                )


@client.event
async def on_ready():

    print(f"Logget inn som {client.user}")

    client.add_view(PrisView())

    data = hent_data()

    for guild in client.guilds:

        kanal = discord.utils.get(
            guild.text_channels,
            name=KANAL_NAVN
        )

        if not kanal:
            continue

        melding = None

        # Prøv å finne den gamle meldingen
        if data.get("melding_id"):

            try:
                melding = await kanal.fetch_message(
                    int(data["melding_id"])
                )

            except discord.NotFound:
                melding = None

        # Hvis ingen melding finnes, lag én
        if melding is None:

            pris = data.get("pris", "normal")

            melding = await kanal.send(
                (
                    "⚡ **STRØMPRIS**\n\n"
                    f"**{PRISER[pris]}**\n\n"
                    "Ingen oppdatering registrert ennå.\n\n"
                    "Trykk på knappen under for å oppdatere."
                ),
                view=PrisView()
            )

            data["melding_id"] = str(melding.id)
            data["pris"] = pris

            lagre_data(data)


client.run(TOKEN)
