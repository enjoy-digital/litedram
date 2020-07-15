from litedram.phy.gensdrphy import GENSDRPHY, HalfRateGENSDRPHY

from litedram.phy.s6ddrphy import S6HalfRateDDRPHY, S6QuarterRateDDRPHY
from litedram.phy.s7ddrphy import V7DDRPHY, K7DDRPHY, A7DDRPHY
from litedram.phy.usddrphy import USDDRPHY, USPDDRPHY

from litedram.phy.ecp5ddrphy import ECP5DDRPHY, ECP5DDRPHYInit

# backward compatibility (remove when no longer needed)
from litedram.phy import s7ddrphy as a7ddrphy
from litedram.phy import s7ddrphy as k7ddrphy
