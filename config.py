import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Bot configuration
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    CHANNEL_ID: int = int(os.getenv("CHANNEL_ID", "0"))
    STAFF_CHAT_ID: int = int(os.getenv("STAFF_CHAT_ID", "0"))

    # Feature flags
    JOIN_REQUESTS_ENABLED: bool = os.getenv("JOIN_REQUESTS_ENABLED", "yes").lower() == "yes"
    DEBUG: bool = os.getenv("DEBUG", "false").lower() == "true"

    # Campaign texts
    CAMPAIGN_HEADER: str = os.getenv("CAMPAIGN_HEADER", "🎯 Havan Academy Challenge\n\n📊 Your Stats:\n👥 Total Invited: {}\n🏆 Your Rank: {}")
    SHARE_BODY: str = os.getenv("SHARE_BODY", (
        "ወሳኝ ነገር Online ለሆናችሁ ፍሬሽማን ተማሪዎች🎉\n\n"
        "ዩኒቨርስቲ ላይ GPA four ማምጣት በጣም ቀላል ነው። ፍሬሽማንን በስኬት አጠናቀው የፈለጉት ዲፓርትመንት የሚገቡ ልጆች ሌት እና ቀን የሚያጠኑት ብቻ አይደሉም።  "
        "ዩኒቨርስቲ ላይ ፈተና ይደጋገማል።ይሄ ማንም የሚያውቀው ነገር ነው ነገር ግን የተደራጁ ፈተናዎችን ማግኘት አስቸጋሪ ከመሆኑ የተነሳ "
        "ሳናስበው ጥያቄዎችን ሳንሰራ እንገባለን። ትልቅ ስህተት!😨\n\n"
        "የዚህ አመት ፍሬሽማኖች በጣም እድለኞች ናችሁ። ሃቫን  በቴሌግራም ላይ የተበተኑትን የmid እና የfinal exam ፈተናዎች "
        "በዩኒቨርስቲ፣ በsubject እና በአመተ ምህረት አደራጅተን እየለቀቅን ነው። 💪\n\n"
        "ከ34.8 ሺ በላይ የፍሬሽማን ተማሪዎች በሚከተሉት የቴሌግራም ቻናላችን ላይ ሁሉንም በነጻ ታገኛላችሁ።👇👇👇\n\n"
        "👉<INVITE_LINK>👆👆\n\n"
        "ከዛሬ ውጭ ሊንኩ አይሰራላችሁም። አሁኑኑ Join በሉ።"
    ))

    def __post_init__(self):
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        if self.CHANNEL_ID == 0:
            raise ValueError("CHANNEL_ID is required")
        if self.STAFF_CHAT_ID == 0:
            raise ValueError("STAFF_CHAT_ID is required")

config = Config()
