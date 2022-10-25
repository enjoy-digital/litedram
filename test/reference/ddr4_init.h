#ifndef __GENERATED_SDRAM_PHY_H
#define __GENERATED_SDRAM_PHY_H

#include <hw/common.h>
#include <generated/csr.h>

#define DFII_CONTROL_SEL 0x01
#define DFII_CONTROL_CKE 0x02
#define DFII_CONTROL_ODT 0x04
#define DFII_CONTROL_RESET_N 0x08

#define DFII_COMMAND_CS 0x01
#define DFII_COMMAND_WE 0x02
#define DFII_COMMAND_CAS 0x04
#define DFII_COMMAND_RAS 0x08
#define DFII_COMMAND_WRDATA 0x10
#define DFII_COMMAND_RDDATA 0x20

#define SDRAM_PHY_USDDRPHY
#define SDRAM_PHY_XDR 2
#define SDRAM_PHY_DATABITS 64
#define SDRAM_PHY_DFI_DATABITS 128
#define SDRAM_PHY_PHASES 4
#define SDRAM_PHY_CL 9
#define SDRAM_PHY_CWL 9
#define SDRAM_PHY_CMD_LATENCY 0
#define SDRAM_PHY_RDPHASE 3
#define SDRAM_PHY_WRPHASE 3
#define SDRAM_PHY_WRITE_LEVELING_CAPABLE
#define SDRAM_PHY_WRITE_LATENCY_CALIBRATION_CAPABLE
#define SDRAM_PHY_READ_LEVELING_CAPABLE
#define SDRAM_PHY_DQ_DQS_RATIO 8
#define SDRAM_PHY_MODULES 8
#define SDRAM_PHY_DELAYS 512
#define SDRAM_PHY_BITSLIPS 8

void cdelay(int i);

__attribute__((unused)) static inline void command_p0(int cmd)
{
	sdram_dfii_pi0_command_write(cmd);
	sdram_dfii_pi0_command_issue_write(1);
}
__attribute__((unused)) static inline void command_p1(int cmd)
{
	sdram_dfii_pi1_command_write(cmd);
	sdram_dfii_pi1_command_issue_write(1);
}
__attribute__((unused)) static inline void command_p2(int cmd)
{
	sdram_dfii_pi2_command_write(cmd);
	sdram_dfii_pi2_command_issue_write(1);
}
__attribute__((unused)) static inline void command_p3(int cmd)
{
	sdram_dfii_pi3_command_write(cmd);
	sdram_dfii_pi3_command_issue_write(1);
}

#define DFII_PIX_DATA_SIZE CSR_SDRAM_DFII_PI0_WRDATA_SIZE

static inline unsigned long sdram_dfii_pix_wrdata_addr(int phase)
{
	switch (phase) {
		case 0: return CSR_SDRAM_DFII_PI0_WRDATA_ADDR;
		case 1: return CSR_SDRAM_DFII_PI1_WRDATA_ADDR;
		case 2: return CSR_SDRAM_DFII_PI2_WRDATA_ADDR;
		case 3: return CSR_SDRAM_DFII_PI3_WRDATA_ADDR;
		default: return 0;
	}
}
static inline unsigned long sdram_dfii_pix_rddata_addr(int phase)
{
	switch (phase) {
		case 0: return CSR_SDRAM_DFII_PI0_RDDATA_ADDR;
		case 1: return CSR_SDRAM_DFII_PI1_RDDATA_ADDR;
		case 2: return CSR_SDRAM_DFII_PI2_RDDATA_ADDR;
		case 3: return CSR_SDRAM_DFII_PI3_RDDATA_ADDR;
		default: return 0;
	}
}

#define DDRX_MR_WRLVL_ADDRESS 1
#define DDRX_MR_WRLVL_RESET 769
#define DDRX_MR_WRLVL_BIT 7

static inline void init_sequence(void)
{
	/* Release reset */
	sdram_dfii_pi0_address_write(0x0);
	sdram_dfii_pi0_baddress_write(0);
	sdram_dfii_control_write(DFII_CONTROL_ODT|DFII_CONTROL_RESET_N);
	cdelay(50000);

	/* Bring CKE high */
	sdram_dfii_pi0_address_write(0x0);
	sdram_dfii_pi0_baddress_write(0);
	sdram_dfii_control_write(DFII_CONTROL_CKE|DFII_CONTROL_ODT|DFII_CONTROL_RESET_N);
	cdelay(10000);

	/* Load Mode Register 3 */
	sdram_dfii_pi0_address_write(0x0);
	sdram_dfii_pi0_baddress_write(3);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 6 */
	sdram_dfii_pi0_address_write(0x0);
	sdram_dfii_pi0_baddress_write(6);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 5 */
	sdram_dfii_pi0_address_write(0x400);
	sdram_dfii_pi0_baddress_write(5);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 4 */
	sdram_dfii_pi0_address_write(0x0);
	sdram_dfii_pi0_baddress_write(4);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 2, CWL=9 */
	sdram_dfii_pi0_address_write(0x200);
	sdram_dfii_pi0_baddress_write(2);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 1 */
	sdram_dfii_pi0_address_write(0x301);
	sdram_dfii_pi0_baddress_write(1);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 0, CL=9, BL=8 */
	sdram_dfii_pi0_address_write(0x100);
	sdram_dfii_pi0_baddress_write(0);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);
	cdelay(200);

	/* ZQ Calibration */
	sdram_dfii_pi0_address_write(0x400);
	sdram_dfii_pi0_baddress_write(0);
	command_p0(DFII_COMMAND_WE|DFII_COMMAND_CS);
	cdelay(200);

}

#endif /* __GENERATED_SDRAM_PHY_H */
