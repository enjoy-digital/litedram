"""
ECC frontend for LiteDRAM

Adds ECC support to Native ports.

Features:
- Single Error Correction.
- Double Error Detection.
- Errors injection.
- Errors reporting.

Limitations:
- Byte enable not supported for writes.
"""

from functools import reduce
from operator import xor

from migen import *

from litex.soc.interconnect.csr import *
from litex.soc.interconnect.stream import *

from litedram.common import wdata_description, rdata_description


def compute_m_n(k):
    m = 1
    while (2**m < (m + k + 1)):
        m = m + 1;
    n = m + k
    return m, n


def compute_syndrome_positions(m):
    r = []
    i = 1
    while i <= m:
        r.append(i)
        i = i << 1
    return r


def compute_data_positions(m):
    r = []
    e = compute_syndrome_positions(m)
    for i in range(1, m + 1):
        if not i in e:
            r.append(i)
    return r


def compute_cover_positions(m, p):
    r = []
    i = p
    while i <= m:
        for j in range(min(p, m - i + 1)):
            r.append(i + j)
        i += 2*p
    return r


class SECDED:
    def place_data(self, data, codeword):
        d_pos = compute_data_positions(len(codeword))
        for i, d in enumerate(d_pos):
            self.comb += codeword[d-1].eq(data[i])

    def extract_data(self, codeword, data):
        d_pos = compute_data_positions(len(codeword))
        for i, d in enumerate(d_pos):
            self.comb += data[i].eq(codeword[d-1])

    def compute_syndrome(self, codeword, syndrome):
        p_pos = compute_syndrome_positions(len(codeword))
        for i, p in enumerate(p_pos):
            pn = Signal()
            c_pos = compute_cover_positions(len(codeword), 2**i)
            for c in c_pos:
                new_pn = Signal()
                self.comb += new_pn.eq(pn ^ codeword[c-1])
                pn = new_pn
            self.comb += syndrome[i].eq(pn)

    def place_syndrome(self, syndrome, codeword):
        p_pos = compute_syndrome_positions(len(codeword))
        for i, p in enumerate(p_pos):
            self.comb += codeword[p-1].eq(syndrome[i])

    def compute_parity(self, codeword, parity):
        self.comb += parity.eq(reduce(xor,
            [codeword[i] for i in range(len(codeword))]))


class ECCEncoder(SECDED, Module):
    def __init__(self, k):
        m, n = compute_m_n(k)

        self.i = i = Signal(k)
        self.o = o = Signal(n + 1)

        # # #

        syndrome = Signal(m)
        parity = Signal()
        codeword_d = Signal(n)
        codeword_d_p = Signal(n)
        codeword = Signal(n + 1)

        # place data bits in codeword
        self.place_data(i, codeword_d)
        # compute and place syndrome bits
        self.compute_syndrome(codeword_d, syndrome)
        self.comb += codeword_d_p.eq(codeword_d)
        self.place_syndrome(syndrome, codeword_d_p)
        # compute parity
        self.compute_parity(codeword_d_p, parity)
        # output codeword + parity
        self.comb += o.eq(Cat(parity, codeword_d_p))


class ECCDecoder(SECDED, Module):
    def __init__(self, k):
        m, n = compute_m_n(k)

        self.enable = Signal()
        self.i = i = Signal(n + 1)
        self.o = o = Signal(k)

        self.sec = sec = Signal()
        self.ded = ded = Signal()

        # # #

        syndrome = Signal(m)
        parity = Signal()
        codeword = Signal(n)
        codeword_c = Signal(n)

        # input codeword + parity
        self.compute_parity(i, parity)
        self.comb += codeword.eq(i[1:])
        # compute_syndrome
        self.compute_syndrome(codeword, syndrome)
        self.comb += If(~self.enable, syndrome.eq(0))
        # locate/correct codeword error bit if any and flip it
        cases = {}
        cases["default"] = codeword_c.eq(codeword)
        for i in range(1, 2**len(syndrome)):
            cases[i] = codeword_c.eq(codeword ^ (1<<(i-1)))
        self.comb += Case(syndrome, cases)
        # extract data / status
        self.extract_data(codeword_c, o)
        self.comb += [
            If(syndrome != 0,
                 # double error detected
                If(~parity,
                    ded.eq(1)
                # single error corrected
                ).Else(
                    sec.eq(1)
                )
            )
        ]


class LiteDRAMNativePortECCW(Module):
    def __init__(self, data_width_from, data_width_to):
        self.sink = sink = Endpoint(wdata_description(data_width_from))
        self.source = source = Endpoint(wdata_description(data_width_to))

        # # #

        for i in range(8):
            encoder = ECCEncoder(data_width_from//8)
            self.submodules += encoder
            self.comb += [
                sink.connect(source, omit={"data", "we"}),
                encoder.i.eq(sink.data[i*data_width_from//8:(i+1)*data_width_from//8]),
                source.data[i*data_width_to//8:(i+1)*data_width_to//8].eq(encoder.o)
            ]
        self.comb += source.we.eq(2**len(source.we)-1)


class LiteDRAMNativePortECCR(Module):
    def __init__(self, data_width_from, data_width_to):
        self.sink = sink = Endpoint(rdata_description(data_width_to))
        self.source = source = Endpoint(rdata_description(data_width_from))
        self.enable = Signal()
        self.sec = Signal(8)
        self.ded = Signal(8)

        # # #

        self.comb +=  sink.connect(source, omit={"data"})

        for i in range(8):
            decoder = ECCDecoder(data_width_from//8)
            self.submodules += decoder
            self.comb += [
                decoder.enable.eq(self.enable),
                decoder.i.eq(sink.data[i*data_width_to//8:(i+1)*data_width_to//8]),
                source.data[i*data_width_from//8:(i+1)*data_width_from//8].eq(decoder.o),
                If(source.valid,
                    self.sec[i].eq(decoder.sec),
                    self.ded[i].eq(decoder.ded)
                )
            ]


class LiteDRAMNativePortECC(Module, AutoCSR):
    def __init__(self, port_from, port_to, with_error_injection=False):
        _ , n = compute_m_n(port_from.data_width//8)
        assert port_to.data_width >= (n + 1)*8

        self.enable = CSRStorage(reset=1)
        self.clear = CSR()
        self.sec_errors = CSRStatus(32)
        self.ded_errors = CSRStatus(32)
        self.sec_detected = sec_detected = Signal()
        self.ded_detected = ded_detected = Signal()
        if with_error_injection:
            self.flip = CSRStorage(8)

        # # #

        # cmd
        self.comb += port_from.cmd.connect(port_to.cmd)

        # wdata (ecc encoding)
        ecc_wdata = LiteDRAMNativePortECCW(port_from.data_width, port_to.data_width)
        ecc_wdata = BufferizeEndpoints({"source": DIR_SOURCE})(ecc_wdata)
        self.submodules += ecc_wdata
        self.comb += [
            port_from.wdata.connect(ecc_wdata.sink),
            ecc_wdata.source.connect(port_to.wdata)
        ]
        if with_error_injection:
            self.comb += port_to.wdata.data[:8].eq(self.flip.storage ^ ecc_wdata.source.data[:8])

        # rdata (ecc decoding)
        sec = Signal()
        ded = Signal()
        ecc_rdata = LiteDRAMNativePortECCR(port_from.data_width, port_to.data_width)
        ecc_rdata = BufferizeEndpoints({"source": DIR_SOURCE})(ecc_rdata)
        self.submodules += ecc_rdata
        self.comb += [
            ecc_rdata.enable.eq(self.enable.storage),
            port_to.rdata.connect(ecc_rdata.sink),
            ecc_rdata.source.connect(port_from.rdata)
        ]

        # errors count
        sec_errors = self.sec_errors.status
        ded_errors = self.ded_errors.status
        self.sync += [
            If(self.clear.re,
                sec_errors.eq(0),
                ded_errors.eq(0),
                sec_detected.eq(0),
                ded_detected.eq(0),
            ).Else(
                If(sec_errors != (2**len(sec_errors) - 1),
                    If(ecc_rdata.sec != 0,
                        sec_detected.eq(1),
                        sec_errors.eq(sec_errors + 1)
                    )
                ),
                If(ded_errors != (2**len(ded_errors) - 1),
                    If(ecc_rdata.ded != 0,
                        ded_detected.eq(1),
                        ded_errors.eq(ded_errors + 1)
                    )
                )
            )
        ]
