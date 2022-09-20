#
# This file is part of LiteDRAM.
#
# Copyright (c) 2015 Sebastien Bourdeauducq <sb@m-labs.hk>
# Copyright (c) 2021 Antmicro <www.antmicro.com>
# SPDX-License-Identifier: BSD-2-Clause

from migen import *
from migen.fhdl.structure import _Slice
from migen.genlib.record import *
from migen.genlib.cdc import PulseSynchronizer

from litedram.common import PhySettings
from litedram.phy.utils import Serializer, Deserializer


def phase_cmd_description(addressbits, bankbits, nranks, with_sub_channels=False):
    common = [
        ("cke",          nranks, DIR_M_TO_S),
        ("reset_n",           1, DIR_M_TO_S),
        ("mode_2n",           1, DIR_M_TO_S),
        ("alert_n",           1, DIR_S_TO_M),
    ]
    prefixes = [""] if not with_sub_channels else ["A_", "B_"]
    temp = []
    for prefix in prefixes:
        temp.append((prefix, [
            ("address", addressbits, DIR_M_TO_S),
            ("bank",       bankbits, DIR_M_TO_S),
            ("cas_n",             1, DIR_M_TO_S),
            ("cs_n",         nranks, DIR_M_TO_S),
            ("ras_n",             1, DIR_M_TO_S),
            ("act_n",             1, DIR_M_TO_S),
            ("odt",               1, DIR_M_TO_S),
            ("we_n",              1, DIR_M_TO_S),
        ]))
    sub_channels = temp[0][1] if not with_sub_channels else temp
    return common + sub_channels


def phase_wrdata_description(databits, with_sub_channels=False):
    prefixes = [""] if not with_sub_channels else ["A_", "B_"]
    _l = len(prefixes)
    temp = []
    for prefix in prefixes:
        temp.append((prefix, [
            ("wrdata",     databits//_l, DIR_M_TO_S),
            ("wrdata_en",             1, DIR_M_TO_S),
            ("wrdata_mask", databits//8, DIR_M_TO_S)]))
    return temp[0][1] if not with_sub_channels else temp


def phase_rddata_description(databits, with_sub_channels=False):
    prefixes = [""] if not with_sub_channels else ["A_", "B_"]
    _l = len(prefixes)
    temp = []
    for prefix in prefixes:
        temp.append((prefix, [
            ("rddata_en",           1, DIR_M_TO_S),
            ("rddata",   databits//_l, DIR_S_TO_M),
            ("rddata_valid",        1, DIR_S_TO_M)]))
    return temp[0][1] if not with_sub_channels else temp


def fixup(layout):
    fixed_up = []
    common = []
    sub_A = []
    sub_B = []
    for signal in layout:
        if signal[0] == "A_":
            sub_A.extend(signal[1])
        elif signal[0] == "B_":
            sub_B.extend(signal[1])
        else:
            common.append(signal)
    return common + [("A_", sub_A)] + [("B_", sub_B)]


def phase_description(addressbits, bankbits, nranks, databits, with_sub_channels=False):
    r = phase_cmd_description(addressbits, bankbits, nranks, with_sub_channels)
    r += phase_wrdata_description(databits, with_sub_channels)
    r += phase_rddata_description(databits, with_sub_channels)
    if with_sub_channels:
        r = fixup(r)
    return r


# Slightly modified migen method, now with support for Slices
def custom_connect(self, *slaves, keep=None, omit=None):
    if keep is None:
        _keep = set([f[0] for f in self.layout])
    elif isinstance(keep, list):
        _keep = set(keep)
    else:
        _keep = keep
    if omit is None:
        _omit = set()
    elif isinstance(omit, list):
        _omit = set(omit)
    else:
        _omit = omit

    _keep = _keep - _omit

    r = []
    for f in self.layout:
        field = f[0]
        self_e = getattr(self, field)
        if isinstance(self_e, Signal):
            if field in _keep:
                direction = f[2]
                if direction == DIR_M_TO_S:
                    r += [getattr(slave, field).eq(self_e) for slave in slaves]
                elif direction == DIR_S_TO_M:
                    r.append(self_e.eq(reduce(or_, [getattr(slave, field) for slave in slaves])))
                else:
                    raise TypeError
        elif isinstance(self_e, _Slice):
            if field in _keep:
                direction = f[2]
                if direction == DIR_M_TO_S:
                    r += [getattr(slave, field).eq(self_e) for slave in slaves]
                elif direction == DIR_S_TO_M:
                    r.append(self_e.eq(reduce(or_, [getattr(slave, field) for slave in slaves])))
                else:
                    raise TypeError
        else:
            for slave in slaves:
                r += self_e.connect(getattr(slave, field), keep=keep, omit=omit)
    return r


Record.connect = custom_connect


class Interface(Record):
    def __init__(self, addressbits, bankbits, nranks, databits, nphases=1, with_sub_channels=False):
        self.with_sub_channels = with_sub_channels
        self.databits = databits
        layout = [("p"+str(i), phase_description(addressbits, bankbits, nranks, databits, with_sub_channels)) for i in range(nphases)]
        Record.__init__(self, layout)
        self.phases = [getattr(self, "p"+str(i)) for i in range(nphases)]
        prefixes = [""] if not with_sub_channels else ["A_", "B_"]
        if not with_sub_channels:
            for p in self.phases:
                setattr(p, "", p)
        for p in self.phases:
            for prefix in prefixes:
                getattr(p, prefix).cas_n.reset = 1
                getattr(p, prefix).cs_n.reset = (2**nranks-1)
                getattr(p, prefix).ras_n.reset = 1
                getattr(p, prefix).we_n.reset = 1
                getattr(p, prefix).act_n.reset = 1
            p.mode_2n.reset = 0

    # Returns pairs (DFI-mandated signal name, Migen signal object)
    def get_standard_names(self, m2s=True, s2m=True):
        r = []
        add_suffix = len(self.phases) > 1
        for n, phase in enumerate(self.phases):
            for field, size, direction in phase.layout:
                if (m2s and direction == DIR_M_TO_S) or (s2m and direction == DIR_S_TO_M):
                    if add_suffix:
                        if direction == DIR_M_TO_S:
                            suffix = "_p" + str(n)
                        else:
                            suffix = "_w" + str(n)
                    else:
                        suffix = ""
                    r.append(("dfi_" + field + suffix, getattr(phase, field)))
        return r

    def create_sub_channels(self):
        if self.with_sub_channels:
            return
        prefixes = ["A_", "B_"]
        self.with_sub_channels = True
        cmd_ = ["address", "bank", "cas_n", "cs_n", "ras_n", "act_n", "odt", "we_n"]
        wrdata_ = ["wrdata", "wrdata_mask"]
        rddata_ = ["rddata", "rddata_valid"]
        nranks = len(self.phases[0].cs_n)
        databits = self.databits
        sub_channel_sig = [
            ("address",  14, DIR_M_TO_S),
            ("bank",      1, DIR_M_TO_S),
            ("cas_n",     1, DIR_M_TO_S),
            ("cs_n", nranks, DIR_M_TO_S),
            ("ras_n",     1, DIR_M_TO_S),
            ("act_n",     1, DIR_M_TO_S),
            ("odt",       1, DIR_M_TO_S),
            ("we_n",      1, DIR_M_TO_S),
            ("wrdata",       databits//2, DIR_M_TO_S),
            ("wrdata_en",              1, DIR_M_TO_S),
            ("wrdata_mask", databits//16, DIR_M_TO_S),
            ("rddata_en",              1, DIR_M_TO_S),
            ("rddata",       databits//2, DIR_S_TO_M),
            ("rddata_valid",           1, DIR_S_TO_M)
        ]
        for p in self.phases:
            for i, prefix in enumerate(prefixes):
                r = Record(sub_channel_sig)
                p.layout.append((prefix, sub_channel_sig))
                setattr(p, prefix, r)
                for cmd in cmd_:
                    setattr(r, cmd, getattr(p, cmd))
                setattr(r, 'wrdata_en', getattr(p, 'wrdata_en'))
                setattr(r, 'wrdata', getattr(p, 'wrdata')[i*databits//2:(i+1)*databits//2])
                setattr(r, 'wrdata_mask', getattr(p, 'wrdata_mask')[i*databits//16:(i+1)*databits//16])
                setattr(r, 'rddata_en', getattr(p, 'rddata_en'))
                setattr(r, 'rddata', getattr(p, 'rddata')[i*databits//2:(i+1)*databits//2])
                setattr(r, 'rddata_valid', getattr(p, 'rddata_valid'))

    def remove_common_signals(self):
        cmd_ = ["address", "bank", "cas_n", "cs_n", "ras_n", "act_n", "odt", "we_n"]
        wrdata_ = ["wrdata", "wrdata_mask", "wrdata_en"]
        rddata_ = ["rddata", "rddata_valid", "rddata_en"]
        new_layout = []
        for phase, signals in self.layout:
            temp = []
            for signal in signals:
                 if signal[0] not in cmd_ + wrdata_ + rddata_:
                    temp.append(signal)
            new_layout.append((phase, temp))
        self.layout = new_layout

        for phase in self.phases:
            for sig in cmd_ + wrdata_ + rddata_:
                delattr(phase, sig)
            new_layout = []
            for signal in phase.layout:
                if signal[0] not in cmd_ + wrdata_ + rddata_:
                    new_layout.append(signal)
            phase.layout = new_layout

    def get_subchannel(self, prefix):
        if prefix == "" and not self.with_sub_channels:
            return self.phases
        if prefix == "":
            raise Exception("DFI interfaces already converted to one with subchannels")
        self.create_sub_channels()
        return [getattr(phase, prefix) for phase in self.phases]


class Interconnect(Module):
    def __init__(self, master, slave):
        self.comb += master.connect(slave)


class DDR4DFIMux(Module):
    def __init__(self, dfi_i, dfi_o):
        for i in range(len(dfi_i.phases)):
            p_i = dfi_i.phases[i]
            p_o = dfi_o.phases[i]
            self.comb += [
                p_i.connect(p_o),
                If(~p_i.ras_n & p_i.cas_n & p_i.we_n,
                   p_o.act_n.eq(0),
                   p_o.we_n.eq(p_i.address[14]),
                   p_o.cas_n.eq(p_i.address[15]),
                   p_o.ras_n.eq(p_i.address[16])
                ).Else(
                    p_o.act_n.eq(1),
                )
            ]


class DFIRateConverter(Module):
    """Converts between DFI interfaces running at different clock frequencies

    This module allows to convert DFI interface `phy_dfi` running at higher clock frequency
    into a DFI interface running at `ratio` lower frequency. The new DFI has `ratio` more
    phases and the commands on the following phases of the new DFI will be serialized to
    following phases/clocks of `phy_dfi` (phases first, then clock cycles).

    Data must be serialized/deserialized in such a way that a whole burst on `phy_dfi` is
    sent in a single `clk` cycle. For this reason, the new DFI interface will have `ratio`
    less databits. For example, with phy_dfi(nphases=2, databits=32) and ratio=4 the new
    DFI will have nphases=8, databits=8. This results in 8*8=64 bits in `clkdiv` translating
    into 2*32=64 bits in `clk`. This means that only a single cycle of `clk` per `clkdiv`
    cycle carries the data (by default cycle 0). This can be modified by passing values
    different than 0 for `write_delay`/`read_delay` and may be needed to properly align
    write/read latency of the original PHY and the wrapper.
    """
    def __init__(self, phy_dfi, *, clkdiv, clk, ratio, serdes_reset_cnt=-1, write_delay=0, read_delay=0):
        assert len(phy_dfi.p0.wrdata) % ratio == 0
        assert 0 <= write_delay < ratio, f"Data can be delayed up to {ratio} clk cycles"
        assert 0 <= read_delay < ratio, f"Data can be delayed up to {ratio} clk cycles"

        self.ser_latency = Serializer.LATENCY
        self.des_latency = Deserializer.LATENCY

        phase_params = dict(
            addressbits = len(phy_dfi.p0.address),
            bankbits = len(phy_dfi.p0.bank),
            nranks = len(phy_dfi.p0.cs_n),
            databits = len(phy_dfi.p0.wrdata) // ratio,
        )
        self.dfi = Interface(nphases=ratio * len(phy_dfi.phases), **phase_params)

        wr_delayed = ["wrdata", "wrdata_mask"]
        rd_delayed = ["rddata", "rddata_valid"]

        for name, width, dir in phase_description(**phase_params):
            # all signals except write/read
            if name in wr_delayed + rd_delayed:
                continue
            # on each clk phase
            for pi, phase_s in enumerate(phy_dfi.phases):
                sig_s = getattr(phase_s, name)
                assert len(sig_s) == width

                # data from each clkdiv phase
                sigs_m = []
                for j in range(ratio):
                    phase_m = self.dfi.phases[pi + len(phy_dfi.phases)*j]
                    sigs_m.append(getattr(phase_m, name))

                ser = Serializer(
                    clkdiv     = clkdiv,
                    clk       = clk,
                    i_dw      = ratio*width,
                    o_dw      = width,
                    i         = Cat(sigs_m),
                    o         = sig_s,
                    reset_cnt = serdes_reset_cnt,
                    name      = name,
                )
                self.submodules += ser

        # wrdata
        for name, width, dir in phase_description(**phase_params):
            if name not in wr_delayed:
                continue
            for pi, phase_s in enumerate(phy_dfi.phases):
                sig_s = getattr(phase_s, name)
                sig_m = Signal(len(sig_s) * ratio)

                sigs_m = []
                for j in range(ratio):
                    phase_m = self.dfi.phases[pi*ratio + j]
                    sigs_m.append(getattr(phase_m, name))

                width = len(Cat(sigs_m))
                self.comb += sig_m[write_delay*width:(write_delay+1)*width].eq(Cat(sigs_m))

                o = Signal.like(sig_s)
                ser = Serializer(
                    clkdiv     = clkdiv,
                    clk       = clk,
                    i_dw      = len(sig_m),
                    o_dw      = len(sig_s),
                    i         = sig_m,
                    o         = o,
                    reset_cnt = serdes_reset_cnt,
                    name      = name,
                )
                self.submodules += ser

                self.comb += sig_s.eq(o)

        # rddata
        for name, width, dir in phase_description(**phase_params):
            if name not in rd_delayed:
                continue
            for pi, phase_s in enumerate(phy_dfi.phases):
                sig_s = getattr(phase_s, name)

                sig_m = Signal(ratio * len(sig_s))
                sigs_m = []
                for j in range(ratio):
                    phase_m = self.dfi.phases[pi*ratio + j]
                    sigs_m.append(getattr(phase_m, name))

                des = Deserializer(
                    clkdiv    = clkdiv,
                    clk       = clk,
                    i_dw      = len(sig_s),
                    o_dw      = len(sig_m),
                    i         = sig_s,
                    o         = sig_m,
                    reset_cnt = serdes_reset_cnt,
                    name      = name,
                )
                self.submodules += des

                if name == "rddata_valid":
                    self.comb += Cat(sigs_m).eq(Replicate(sig_m[read_delay], ratio))
                else:
                    out_width = len(Cat(sigs_m))
                    sig_m_window = sig_m[read_delay*out_width:(read_delay + 1)*out_width]
                    self.comb += Cat(sigs_m).eq(sig_m_window)

    @classmethod
    def phy_wrapper(cls, phy_cls, ratio, phy_attrs=None, clock_mapping=None, **converter_kwargs):
        """Generate a wrapper class for given PHY

        Given PHY `phy_cls` a new Module is generated, which will instantiate `phy_cls` as a
        submodule (self.submodules.phy), with DFIRateConverter used to convert its DFI. It will
        recalculate `phy_cls` PhySettings to have correct latency values.

        Parameters
        ----------
        phy_cls : type
            PHY class. It must support a `csr_cdc` argument (function: csr_cdc(Signal) -> Signal)
            that it will use to wrap all CSR.re signals to avoid clock domain crossing problems.
        ratio : int
            Frequency ratio between the new DFI and the DFI of the wrapped PHY.
        phy_attrs : list[str]
            Names of PHY attributes to be copied to the wrapper (self.attr = self.phy.attr).
        clock_mapping : dict[str, str]
            Clock remapping for the PHY. Defaults to {"sys": f"sys{ratio}x"}.
        converter_kwargs : Any
            Keyword arguments forwarded to the DFIRateConverter instance.
        """
        if ratio == 1:
            return phy_cls

        # Generate the wrapper class dynamically
        name = f"{phy_cls.__name__}Wrapper"
        bases = (Module, object, )

        internal_cd = f"sys{ratio}x"
        if clock_mapping is None:
            clock_mapping = {"sys": internal_cd}

        # Constructor
        def __init__(self, *args, **kwargs):
            # Add the PHY in new clock domain,
            self.internal_cd = internal_cd
            phy = phy_cls(*args, csr_cdc=self.csr_cdc, **kwargs)

            # Remap clock domains in the PHY
            # Workaround: do this in two steps to avoid errors due to the fact that renaming is done
            # sequentially. Consider mapping {"sys": "sys2x", "sys2x": "sys4x"}, it would lead to:
            #   sys2x = sys
            #   sys4x = sys2x
            # resulting in all sync operations in sys4x domain.
            mapping = [tuple(i) for i in clock_mapping.items()]
            map_tmp = {clk_from: f"tmp{i}" for i, (clk_from, clk_to) in enumerate(mapping)}
            map_final = {f"tmp{i}": clk_to for i, (clk_from, clk_to) in enumerate(mapping)}
            self.submodules.phy = ClockDomainsRenamer(map_final)(ClockDomainsRenamer(map_tmp)(phy))

            # Copy some attributes of the PHY
            for attr in phy_attrs or []:
                setattr(self, attr, getattr(self.phy, attr))

            # Insert DFI rate converter to
            self.submodules.dfi_converter = DFIRateConverter(phy.dfi,
                clkdiv      = "sys",
                clk         = self.internal_cd,
                ratio       = ratio,
                write_delay = phy.settings.write_latency % ratio,
                read_delay  = phy.settings.read_latency % ratio,
                **converter_kwargs,
            )
            self.dfi = self.dfi_converter.dfi

            # Generate new PhySettings
            converter_latency = self.dfi_converter.ser_latency + self.dfi_converter.des_latency
            self.settings = PhySettings(
                phytype                   = phy.settings.phytype,
                memtype                   = phy.settings.memtype,
                databits                  = phy.settings.databits,
                dfi_databits              = len(self.dfi.p0.wrdata),
                nranks                    = phy.settings.nranks,
                nphases                   = len(self.dfi.phases),
                rdphase                   = phy.settings.rdphase,
                wrphase                   = phy.settings.wrphase,
                cl                        = phy.settings.cl,
                cwl                       = phy.settings.cwl,
                read_latency              = phy.settings.read_latency//ratio + converter_latency,
                write_latency             = phy.settings.write_latency//ratio,
                cmd_latency               = phy.settings.cmd_latency,
                cmd_delay                 = phy.settings.cmd_delay,
                write_leveling            = phy.settings.write_leveling,
                write_dq_dqs_training     = phy.settings.write_dq_dqs_training,
                write_latency_calibration = phy.settings.write_latency_calibration,
                read_leveling             = phy.settings.read_leveling,
                delays                    = phy.settings.delays,
                bitslips                  = phy.settings.bitslips,
            )

            # Copy any non-default PhySettings (e.g. electrical settings)
            for attr, value in vars(self.phy.settings).items():
                if not hasattr(self.settings, attr):
                    setattr(self.settings, attr, value)

        def csr_cdc(self, i):
            o = Signal()
            psync = PulseSynchronizer("sys", self.internal_cd)
            self.submodules += psync
            self.comb += [
                psync.i.eq(i),
                o.eq(psync.o),
            ]
            return o

        def get_csrs(self):
            return self.phy.get_csrs()

        # This creates a new class with given name, base classes and attributes/methods
        namespace = dict(
            __init__ = __init__,
            csr_cdc  = csr_cdc,
            get_csrs = get_csrs,
        )
        return type(name, bases, namespace)
