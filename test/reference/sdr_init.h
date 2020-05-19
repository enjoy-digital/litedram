#ifndef __GENERATED_SDRAM_PHY_H
#define __GENERATED_SDRAM_PHY_H
#include <hw/common.h>
#include <generated/csr.h>

#define DFII_CONTROL_SEL        0x01
#define DFII_CONTROL_CKE        0x02
#define DFII_CONTROL_ODT        0x04
#define DFII_CONTROL_RESET_N    0x08

#define DFII_COMMAND_CS         0x01
#define DFII_COMMAND_WE         0x02
#define DFII_COMMAND_CAS        0x04
#define DFII_COMMAND_RAS        0x08
#define DFII_COMMAND_WRDATA     0x10
#define DFII_COMMAND_RDDATA     0x20

#define SDRAM_PHY_GENSDRPHY
#define SDRAM_PHY_PHASES 1

static void cdelay(int i);

__attribute__((unused)) static void command_p0(int cmd)
{
    sdram_dfii_pi0_command_write(cmd);
    sdram_dfii_pi0_command_issue_write(1);
}


#define sdram_dfii_pird_address_write(X) sdram_dfii_pi0_address_write(X)
#define sdram_dfii_piwr_address_write(X) sdram_dfii_pi0_address_write(X)
#define sdram_dfii_pird_baddress_write(X) sdram_dfii_pi0_baddress_write(X)
#define sdram_dfii_piwr_baddress_write(X) sdram_dfii_pi0_baddress_write(X)
#define command_prd(X) command_p0(X)
#define command_pwr(X) command_p0(X)

#define DFII_PIX_DATA_SIZE CSR_SDRAM_DFII_PI0_WRDATA_SIZE

const unsigned long sdram_dfii_pix_wrdata_addr[SDRAM_PHY_PHASES] = {
	CSR_SDRAM_DFII_PI0_WRDATA_ADDR
};

const unsigned long sdram_dfii_pix_rddata_addr[SDRAM_PHY_PHASES] = {
	CSR_SDRAM_DFII_PI0_RDDATA_ADDR
};

static void init_sequence(void)
{
	/* Bring CKE high */
	sdram_dfii_pi0_address_write(0x0);
	sdram_dfii_pi0_baddress_write(0);
	sdram_dfii_control_write(DFII_CONTROL_CKE|DFII_CONTROL_ODT|DFII_CONTROL_RESET_N);
	cdelay(20000);

	/* Precharge All */
	sdram_dfii_pi0_address_write(0x400);
	sdram_dfii_pi0_baddress_write(0);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register / Reset DLL, CL=2, BL=1 */
	sdram_dfii_pi0_address_write(0x120);
	sdram_dfii_pi0_baddress_write(0);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);
	cdelay(200);

	/* Precharge All */
	sdram_dfii_pi0_address_write(0x400);
	sdram_dfii_pi0_baddress_write(0);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Auto Refresh */
	sdram_dfii_pi0_address_write(0x0);
	sdram_dfii_pi0_baddress_write(0);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_CS);
	cdelay(4);

	/* Auto Refresh */
	sdram_dfii_pi0_address_write(0x0);
	sdram_dfii_pi0_baddress_write(0);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_CS);
	cdelay(4);

	/* Load Mode Register / CL=2, BL=1 */
	sdram_dfii_pi0_address_write(0x20);
	sdram_dfii_pi0_baddress_write(0);
	command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);
	cdelay(200);

}
#endif
