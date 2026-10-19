# UltraScale native DDR PHY development

The package includes native primitive generators and an experimental complete
`USNativeDDRPHY` using logical calibration ABI v1. The complete PHY requires
Vivado and the matching LiteX BIOS. Its integrated datapath/calibration currently
requires single-rank x16 DDR4, two x8 lanes with masks and the documented
command/address geometry. Wider generator simulations are not evidence of a
complete wider PHY or hardware qualification.

`USNativeDDRPHY` queries the selected Vivado installation, validates the maps,
and generates the native core. Queries are fresh by default; `query_cache_dir`
enables validated local reuse and `query_force_refresh=True` bypasses it.
Caches include tool, part, pins and query-source identities, and are local build
artifacts. Never commit queried maps, logs, caches or generated physical wiring.

`NativeMapping` assigns compact logical tap and control IDs from the validated
core layout. The adapter uses those same IDs for delay control, FIFO status,
read gating and RIU selection; BIOS does not interpret physical site numbers.
The `usnative_mapping` PHY setting generates `SDRAM_PHY_USNATIVE_*` definitions
in `sdram_phy.h`. Read-only `abi_version`, `abi_config_id` and
`abi_capabilities` CSRs let BIOS reject mismatched firmware before training.
An incompatible contract increments the major version; additive extensions
increment the minor version and declare required capabilities. The configuration
ID covers logical geometry and the operating profile; it is a stale-build check,
not cryptographic authentication. Logical descriptors contain no package pins,
banks, native site names or captured device database records.

Unsupported integrated geometry, rates and non-Vivado toolchains fail before
querying. Additional boards require their own build and hardware validation;
family recognition alone is not qualification.

Supported initial profiles are 2400 and 2666.667 MT/s. The 2933.333 and 3200 MT/s
profiles require explicit `overclock=True`; their native delay-model parameter
remains capped at 2666.666667 MHz while clock constraints retain the actual
frequency. These are experimental overclocks, not device-rated configurations
or automatic timing exceptions. The packaged integration requires its own
implementation and hardware validation; previous local builds are not proof.

Debug trace hardware is opt-in. DMA testing is a separate optional frontend,
`litedram.frontend.native_benchmark.NativeDMABenchmark`. Increasing a DMA port
from 128 to 256 bits does not widen the physical DDR interface or change the
PHY ratio. Converted-port write timing measures acceptance into that port;
there is a settling interval before integrity reads, but no DDR write-response
channel. Do not interpret this as a durability/completion guarantee.

Existing PHY implementations and defaults are unchanged. DDR4 initialization
now uses tWR rather than tWTR when encoding MR0 write recovery; the native
profile also selects tCCD_L=8 in MR6 to match its controller configuration.

## Pin extraction

`litedram.phy.usnative.pins.extract_ddr_pins(platform, pads)` takes an already
requested DDR4 resource and returns an immutable package-pin map. It uses LiteX's
resolved constraints, including connector aliases, and matches signal identity
so unrelated resources and other memory channels are excluded. No board module
is imported by the PHY package.

```python
from litedram.phy.usnative.pins import extract_ddr_pins

pads = platform.request("ddram", 0)
pin_map = extract_ddr_pins(platform, pads)
manifest = pin_map.to_dict()
```

Extraction rejects unsupported device families, missing DDR4 signals, duplicate
or unresolved pins, inconsistent widths and absent I/O standards. x4 and x8 DQS
grouping are represented, including the Alveo x4 layouts. This is input
validation, not proof of native topology legality. Part existence, bank types,
differential pairing, byte/nibble sites and clock routes require Vivado queries.

The input fingerprint changes with the part, pins and I/O standards. Local
query caching additionally includes the query schema/source and Vivado version.
The fingerprint alone does not validate a cached physical map.

## Vivado physical topology

`litedram.phy.usnative.topology.vivado_query(pin_map)` emits Tcl defining
`usnative_query output_path`. Source it in an open design for the matching part
and call the procedure to export a tab-separated map. The caller owns tool
execution and must reject a failed Vivado run. This low-level emitter does
not start a process; `query_device()` runs both queries and checks their
results. Cache reuse requires explicit configuration and revalidates the stored
responses; force-refresh is available for an independent discovery run.

The query uses package-pin differential partners and byte-position properties.
It follows the device connections from IOB transmit/receive pins to native
RXTX sites and from the dynamic DCI input to the nibble controller. It does not
infer native coordinates from IOB coordinates. See AMD's
[device-node queries](https://docs.amd.com/r/2022.2-English/ug835-vivado-tcl-commands/get_nodes)
and [package byte groups](https://docs.amd.com/r/2023.1-English/ug912-vivado-properties/PKGPIN_BYTEGROUP).

`parse_vivado_map(pin_map, text, vivado_version=...)` checks the input fingerprint,
part, schema, required tool version, completion marker and exact pin coverage.
It rejects invalid differential polarity/pairing, unsuitable DQS sites,
inconsistent bank/byte/nibble metadata, duplicate native sites, conflicting
control sites and data/masks outside their strobe groups. HP single-ended command
sites are accepted. This does not validate clock routing, electrical settings,
timing closure or the complete DDR initialization/calibration path.

Live device-map checks cover XEM8320 (Vivado 2026.1), KCU116 (2025.2), and
original UltraScale KCU105 (2019.1 and 2025.2). Local KCU105 x64 DDR4-2400
integrations have passed full implementation with both tools; KCU105 hardware
calibration remains untested. Family eligibility alone is not hardware support.
Some placed component-mode designs expose different site modes;
an unplaced synthesized design is the preferred query context.

## RXTX serializer generation

`litedram.phy.usnative.rxtx.emit_rxtx()` emits a located `RXTX_BITSLICE` wrapper
from a validated native site, signal role, FPGA family and reference frequency.
The initial profile uses eight-bit serialization and variable TIME delays.
Data/DM, DQS, command/address and CK roles select the corresponding native
parameters. Every primitive port remains explicit, including delay controls,
FIFO status and native control buses. Pre-emphasis is an explicit option.

This emitter does not generate clock distribution, bitslice controllers,
tristate controllers, I/O buffers or calibration. The caller must provide them
and validate complete device topology and timing. Accepting a frequency does
not establish that it meets device ratings.

The local XEM8320 integration replaces 45 RXTX instances while retaining its
existing control/tristate wiring and standalone calibration. It compares every
parameter and named connection against the working 2666.667 MT/s reference
before synthesis. Integration artifacts and qualification records are kept
outside this repository.

## Native control generation

`litedram.phy.usnative.control.control_profiles()` derives per-control settings
from the validated physical map. Data nibbles enable receive/transmit gating and
90-degree receive clocks; a data nibble whose DQS belongs to its byte partner
enables the other-nibble clocks. Command-only controls disable these features.
Output commands can share a data control, as on the XEM8320, but their RXTX role
configuration still belongs to the caller. Multiple strobe sources in one
control and cross-byte strobe use are rejected. The initial x4 profile uses
local strobes; DM-to-x4 grouping requires future explicit mapping.

`emit_control()` exposes all native control, readiness, RIU and clock ports.
North/south external clock forwarding is disabled in this profile. The emitter
does not establish complete clock legality or generate inter-primitive wiring;
the local integration checks that wiring against its working reference.

## Tristate and RIU generation

`vivado_auxiliary_query()` and `parse_auxiliary_map()` in `auxiliary.py` map
validated controls to their dedicated tristate and RIU sites. The query follows
device nodes for tristate reset/delay outputs and all 16 RIU data bits. The
parser verifies the device/tool/pin-map identity, complete control coverage,
unique tristates, shared byte RIU sites and correct LOW/UPP nibble assignments.
The caller must check Vivado's exit status before using the exported map.

`emit_tristate()` in `aux_primitives.py` emits the initial 4:1 fixed TIME-delay
profile with explicit reset/VTC and native control ports. `riu_or()` instantiates
the dedicated byte combiner at its queried location and checks all port widths.
The caller supplies LOW/UPP buses, handles unused halves, and ensures exclusive
RIU transactions. These are primitive building blocks: full bank wiring,
external clock forwarding and complete clock-route validation remain pending.

## Native control-bus wiring

`bank.control_wiring()` derives the 40-bit RX/TX control-bus endpoints from
validated pin and auxiliary maps. Lower-nibble positions 0..5 use controller
slots 0..5; upper-nibble positions 6..12 use slots 0..6. Each serializer has
separate buses to and from its controller for RX and TX, and each tristate
primitive has two control buses. Unused controller input slots are tied low.
Slot collisions, duplicate serializer/tristate sites and missing associations
are rejected. Native-site coordinate offsets are not assumed.

The result provides wire declarations and explicit per-site port connections.
It does not generate clocks, data packing, FIFO control, RIU arbitration or
reset sequencing. Those remain separate integration work. The local XEM8320
adapter compares both endpoints and every bit of each bus with its reference
before replacing the old scalar connections.

## Partner-nibble clocks

`clocks.nibble_clock_wiring(sites, family=...)` derives PCLK/NCLK connections
between controls in opposite nibbles of the same physical bank and byte. It
uses the validated pin map, never control-site coordinate offsets. The plan
records whether each sink enables the borrowed strobe. Both directions are
retained for populated pairs; a lone control with a local strobe or only
commands ties unused partner inputs low. Conflicting physical associations
and unsupported families are rejected.

This covers only partner-nibble connections. Shared PLL routing, external
north/south forwarding, FIFO clocks and sequencing remain the caller's
responsibility. Unit tests do not establish device routing legality; the local
XEM8320 adapter compares every source/sink against the working reference and
requires routed-clock, implementation and hardware checks for each candidate.

## Tests

`core.emit_core()` generates complete primitive-core interconnect from validated
maps: compact data/control arrays, per-bank PLL inputs, FIFO clocks/enables,
reset/VTC inputs, partner clocks and dedicated RIU combiners. Every native input
must have exactly one generated connection. It imports no reference RTL. The
caller supplies PLLs, sequenced resets, I/O buffers, registered transaction
launch and calibration. KCU116 x32 core synthesis in Vivado 2025.2 passed with
65 RXTX slices, 13 controls/tristates and seven RIU combiners; this is an
out-of-context synthesis result, not routed or hardware qualification.

`sidebands.sideband_plan()` explicitly assigns optional PAR and ALERT ownership
and checks supplied MR2/MR5 values for disabled write CRC and CA parity.
`NativeSidebands` drives PAR low and exposes synchronized active/sticky ALERT
status, gated by an explicit `enable` input that defaults low. The sideband plan
identifies ALERT on BITSLICE0/6 in an active native byte. Such a pin needs
`UNAVAILABLE_DURING_CALIBRATION TRUE` and monitoring must remain masked until
BISC readiness has synchronized; expose validity separately from activity.
ALERT is level monitoring, not guaranteed narrow-pulse capture or error
recovery. The integrator must verify actual initialization values and prevent
software from enabling unsupported parity/CRC later. Unhandled sidebands still
fail closed in `native_layout()`.

`layout.native_layout()` assigns compact serializer, control, lane and RIU
indices from validated physical maps. Lane ownership uses logical DQ indices;
native site coordinates are not calibration addresses. The initial layout
requires x8 strobe groups. Raw parity/alert signals fail explicitly: callers
must first assign their ownership with `sideband_plan()`. The saved KCU116 maps
pass complete native-layout validation after that explicit partition.

`fifo.NativeFIFORead` drains all lanes together during controller access. A
single empty DQ FIFO stalls the whole word. Independent draining requires both
software ownership and an explicit enable. Readiness gates every read, and
per-lane counters support diagnostics. The caller supplies native FIFO EMPTY
status in its read-clock domain; this module does not establish clock legality.

`data.NativeDataPacking` maps four double-edge DFI phases to eight-bit native
words, including active-low DM, and reconstructs read data. Bitslip, transaction
launch registers, DQS, command packing and read-valid timing remain separate.
Tests check x16/x32/x64 data ordering and mask polarity, and x16/x32 FIFO
backpressure/ownership. These components are not yet wired into a complete PHY.

Run with the existing LiteDRAM test environment:

```text
python -m unittest test.test_usnative test.test_usnative_topology test.test_usnative_rxtx test.test_usnative_control test.test_usnative_auxiliary test.test_usnative_bank test.test_usnative_clocks test.test_usnative_boards test.test_usnative_layout test.test_usnative_data test.test_usnative_core test.test_dfi test.test_phy_utils
```

The new unit tests exercise family rejection, connector resolution, widths,
duplicate/unassigned pins, missing constraints and channel isolation. The
optional LiteX-Boards tests cover channel zero of 20 DDR4 candidates in
`test/reference/usnative_boards.json`. They skip when LiteX-Boards is absent;
the additional DDR3 candidate is explicitly deferred. Other memory channels
and configurations still require qualification.

Passing extraction does not qualify a board as supported. Hardware tests must
identify the exact image and operating point, retain failures and distinguish
normal timing closure from explicit overclock experiments.

## Incremental integration and hardware gates

1. Pin extraction and family eligibility (this increment).
2. Vivado device mapping and grouping checks (this increment). Full clock-route
   validation and rejection of unintended generated primitive pins remain work
   for the generator integration.
3. Native primitive generation and optional PHY integration. Start with XEM8320,
   then exercise wider and multi-bank layouts on KCU116.
4. Portable standalone calibration with bounded reset/readiness handling,
   repeated window searches, per-DQ read/write deskew and minimum-margin checks.
5. Temperature telemetry, safe exclusive-access maintenance, and verified cached
   fast boot. Thermal qualification remains a separate acceptance requirement.

Use existing DFI, PHY, initialization and DMA tests where applicable. For each
hardware-affecting increment, build the candidate, verify timing/DRC, then run
repeated initialization and counter/PRBS DMA integrity tests on the same board
and frequency as its baseline. Expand testing to margin scans and thermal
transitions when those features change. Keep code, stack and required interrupt
paths outside DDR during maintenance, drain all masters, preserve refresh and
never run destructive boot training against live application memory.

Generated artifacts and local hardware logs belong outside the PR checkout.
Do not attach unchanged-baseline hardware passes to a newly generated image.

## Final transmit register stage

The local XEM8320 integration has hardware-qualified a register stage after
command packing and TX bitslip selection at 2666.667 MT/s. All eight baseline
Route 35-4573 warnings were eliminated; routed checks confirmed direct FF
drivers, and four commanded calibrations plus 16 DMA cases passed. A portable PHY
must retain the relative timing of command, DQ/DM, DQS, tristate/output enables
and receive gate, and account for the added cycle in read-valid latency. A
register on only the flagged data bits would corrupt the serialized word.
Require actual routed sequential-driver checks and unsuppressed warning logs,
then fresh calibration and DMA verification. This stage is not yet part of the
portable building blocks above. Thermal testing is currently deferred by user
request and must not be reported as completed.

## Planned portability and operating-point regression

The local 2933.333 MT/s rebuild passed four commanded calibrations and 16 DMA
cases with the registered TX stage and a separately tested refresh-request
pipeline in the local controller. Its fabric setup/hold margins are
0.000/+0.010 ns; eight native minimum-period violations remain. This is an
explicit overclock result, not normal device timing qualification or a portable
PHY implementation. Two earlier implementation attempts failed fabric timing
and were not programmed. The subsequent 3200 MT/s rebuild also passed four
commanded calibrations, operating-phase readbacks and 16 DMA cases with zero
crosstalk warnings. Its fabric margins are +0.006/+0.010 ns; 54 native period
and 32 pulse checks plus the 1600 MHz versus 1500 MHz VCO limit remain explicit
overclock exceptions. Both rates passed +/-4 RX-tap guards; minimum observed
RX spans were 22 taps at 2933 and 12 at 3200. These are bounded RX scans, not
full TX-eye or thermal qualification. Preserve raw failures and image identity;
historical results never qualify a new image.
The clean-PR priority is then KCU116 x32 (2400, then 2666.667 MT/s), followed by
one VCU118 x64 LiteX channel at 2400 MT/s and original UltraScale on KCU105 x64
at a conservatively selected rate once the device database is available.

Wider builds require complete generic bank/clock/data/FIFO/reset/RIU wiring,
parameterized lane counts and calibration state, explicit parity/alert handling,
and matching controller/DMA widths. Existing PHY defaults must be preserved.
Each candidate requires appropriate simulation, routed timing/DRC and direct
registered-driver checks. Hardware qualification additionally requires repeated
calibration, per-bit margins, full-memory counter/PRBS DMA and CPU interoperability.
Build-only boards remain unqualified for hardware support. Add bounded startup
waits/retries, clear failure reasons and reboot automation incrementally.
Thermal testing remains deferred.

The local KCU116 x32 complete-system integration has now passed normal Vivado
2025.2 implementation at 2400 and 2666.667 MT/s. Both images have a 256-bit native
port and 1:4 PHY/controller ratio; CPU runs at half controller frequency, and
the accepted 2666.667 image also moves its cache/bridge to that slower domain.
Setup/hold margins are +0.061/+0.011 ns and +0.047/+0.010 ns respectively; the
higher-rate pulse/period margin is 0.000 ns at report precision. Final DRC,
clock coverage, all 520 serializer input driver checks and zero critical or
crosstalk warnings passed. The complete PHY/firmware remains local integration,
outside this package; KCU116 calibration, physical eyes and DMA bandwidth have
not been tested on hardware. Digital controller/DMA tests and a cache/CDC test
with masked writes, dirty eviction and concurrent DMA passed. True 1:8 controller
support remains future work; eight-bit serialization is not an eight-CK cycle.

The local VCU118 x64 / 512-bit integration exposed a cross-bank FIFO timing
limit: native FIFO_EMPTY through the all-DQ reduction back to FIFO_RD_EN missed
setup by 0.181 ns at 300 MHz. `NativeFIFORead(..., registered=True)` is an
optional conservative timing mode that registers drain requests and requires
an idle cycle after each read. The idle cycle prevents reuse of a stale EMPTY
sample after consuming a last word. Default draining behavior is unchanged.
Callers must limit arrivals to one word per two read-clock cycles and account
for an additional read cycle; the local candidate enforces tCCD>=2 controller
cycles and uses read latency 13. This is not a full-rate elastic alignment
implementation. Native FIFO flag timing and fixed DFI latency still require
hardware qualification. x16/x32/x64 queue-model tests cover skew, stalls,
underflow, ordering, rate, readiness and software-only lane ownership.

The corrected VCU118 candidate passed normal Vivado 2025.2 signoff with
setup/hold/pulse margins +0.010/+0.011/+0.039 ns and all 840 serializer input
drivers checked. Final review corrected bank 71's implemented reference voltage
from 0.600 to the intended 0.840 V, cleared the DRC conflict, and repeated
signoff/bit generation using the same routed logic. No critical or crosstalk
warnings remain. Digital validation totals 122 passes and one expected skip.
This conservative mode limits scheduling/draining to 9.6 GB/s before overhead
against 19.2 GB/s raw bandwidth; hardware calibration, read latency and actual
throughput remain untested. The 10 ps setup margin motivates placement/skew
improvements before increasing speed. Full-rate elastic buffering, bank-aware
voltage audits and startup recovery remain planned work.

## Subsequent portability and robustness building blocks

Device queries now use SITE_TYPE, which is available in Vivado 2019.1 as well
as 2025.2. The original UltraScale HPIOB site type is accepted only for that
family; package polarity, bank, byte, nibble and actual native connectivity
remain independently checked. KCU105 physical/auxiliary queries pass under
2019.1. Repeated VCU118 queries under 2025.2 produce byte-identical maps.

`NativeCalibrationGuard` invalidates traffic permission on readiness loss or
retraining and requires a fresh successful-calibration commit to re-arm. A
commit held across a fault cannot re-arm it. Diagnostic clear does not grant
permission. Integrators must gate command admission and quiesce/reset in-flight
controller transactions; the guard alone does not implement recovery.

`NativeReadAssembler` buffers independent ordered byte-lane streams and joins
them into 128/256/512-bit words. Digital tests cover random lane skew and output
backpressure, flush of partial words, and sustained one-word-per-cycle output.
Its input is a fabric valid/ready interface, not a native FIFO port. A native
adapter still needs credit reservations for outstanding reads, qualified Q
latency/bitslip, DFI ordering/latency and safe reset epochs. The buffered FIFOs
include an output register in addition to the requested RAM depth. Neither new
building block is wired into the accepted images or hardware qualified yet.

## Registered FIFO timing and RIU transactions

`NativeFIFORead(..., registered=True)` captures per-lane availability before
combining lanes. It samples the software/independent mode with those bits, so
mode changes preserve the original pending-drain semantics. This retimes the
existing register; it adds neither a latency cycle nor another bubble. The
default unregistered path is unchanged. Registered mode still permits at most
one word every two read-clock cycles; it is not a full-rate native FIFO adapter.

`RIUTransaction(controls, riu_indices, timeout=255)` in `riu_transaction` accepts
one outstanding read or write. `riu_indices` maps each control to its shared
RIU byte readback. The requester uses the `sys` domain and the native side uses
`riu`; a caller can rename both domains with Migen's `ClockDomainsRenamer`.
The tested integrations use related, fully timed clocks with sys twice RIU.
Do not treat this helper as permission to false-path the held payload or reply.

`request` is a one-cycle sys-domain strobe; it captures address, data, write flag
and control selection. Busy
requests cannot replace that payload. The helper waits for native VALID,
holds the selected transaction through settling, rechecks VALID, captures a
fresh readback and acknowledges completion. `valid`, `busy` and `error` belong
to this transaction, rather than merely exposing a native readiness level.
Invalid selection and missing readiness terminate with error. The timeout
parameter bounds waits in individual states, not the complete request latency.
Software must still use a bounded end-to-end poll. Soft reset cancels a response
and drains the handshake; it cannot undo a write already presented to native
hardware or guarantee that cancellation arrives before a pending native write.
Related-domain reset and controller recovery remain caller duties.

`RIUFallingLaunch(transaction, platform)` coherently launches the transaction's
address, select, data and write flag on the falling edge of the same RIU clock.
Native controls retain their original rising-edge clock. The included Verilog
register starts at zero and has no separate reset, preserving values at each
native rising-edge sample when transaction registers reset. Both half-cycle
paths must pass static timing. Integration signoff must trace every native RIU
input to the intended falling-edge register or constant; simulation alone does
not establish hold closure.

`RegisteredTapStatus(entries)` captures nine-bit native counters in RIU, then
uses a registered selection tree in sys. `change` must cover every selection
and delay-control update. `valid` stays low for 32 sys cycles after a change or
loss of readiness. The interval covers the tested 2:1 clock relationship and
digital pipeline, not arbitrary clock ratios or analog settling guarantees.
Read data only when valid and after any required native operation settling.

These helpers do not modify existing PHY defaults. The complete XEM8320
`USNativeDDRPHY` integrates the RIU transaction and tap-status helpers; the
calibration guard and elastic assembler remain separate building blocks.
The optional DMA benchmark is included as a frontend. Clock, CPU reset and
Vivado strategy integration belong to the target, and BIOS calibration belongs
to LiteX. Original UltraScale/UltraScale+ eligibility and physical topology
checks still apply;
DDR3, x4 native integration, ECC and a true 1:8 controller remain unsupported.

## Optional paired bank-group DMA

`ControllerSettings(with_bank_group_interleaving=True)` enables an initial
x16 DDR4 profile with four DFI phases, two bank groups, one rank, ten column
bits and tCCD_L=8 CK. The controller preserves long timing for recovery and
turnaround calculations, while CAS arbitration allows tCCD_S=4 CK between
opposite groups and enforces tCCD_L=8 CK within each group. Other controller
configurations retain their existing scheduling and mapping by default.

The option changes physical address mapping for **every** crossbar master:
the lowest 128-bit-word address bit selects BG, followed by seven column bits,
two bank-address bits and row bits. CPU and DMA therefore see the same memory.
Memory contents are not portable between bitstreams with different mappings.
The option also registers row-hit lookahead, crossbar ownership and refresh
countdown status to shorten fabric paths; it does not relax DDR timing.

`litedram.frontend.paired.PairedPort([port0, port1], "write" | "read")` combines
two matching 128-bit sys-domain native masters into one 256-bit `.port`.
Adjacent halves address opposite bank groups. Read credits reserve space for
in-flight responses and preserve ordering under asymmetric returns. Writes
reserve each half's data before issuing its command. Connect the write adapter's
`.drained` to `NativeDMABenchmark(..., drained=...)` so write-cycle measurement
includes both child queues draining to their native ports. The existing settling
interval still follows; native acceptance is not a DDR write-completion response.

This diagnostic endpoint accepts **full-word writes only**. An invalid mask
sets sticky `.error` and discards the word before either child can issue it.
The write adapter then blocks new commands and discards data for any remaining
accepted addresses. Previously issued good writes continue to drain. The caller
must supply the remaining data beats for accepted addresses before `.drained`
can assert; `.drained` with `.error` set indicates an aborted transfer, not a
successful write of every accepted command. Read overflow or unsolicited
responses also set `.error`. Gate new benchmark admission on both
adapters' errors and require system quiescence/reconfiguration after a fault;
resetting an adapter alone cannot cancel already scheduled traffic.

The partial-mask rejection path is currently qualified by digital simulation.
Its additional mask/error gating still requires routed timing checks and board
testing; results from bitstreams built before this change do not qualify it.
The concurrent-traffic regression models CPU-side native requests, not CPU
instructions, caches, or an analog DDR eye.

The board option remains separate from ordinary 256-bit width conversion.
Digital tests exercise asymmetric backpressure, counter/PRBS corruption,
credit exhaustion, drain/error behavior, same/different-group CAS spacing,
refresh timing, and CPU/native mapping through the complete controller and
LiteDRAM PHY model. These tests do not establish hardware bandwidth or margin.
