#ifndef __GENERATED_SDRAM_PHY_H
#define __GENERATED_SDRAM_PHY_H

#include <hw/common.h>
#include <generated/csr.h>
#include <hw/flags.h>
#include <stdint.h>

#define DFII_NPHASES_MAX       4
#define DFII_PIX_DATA_SIZE_MAX 16

static void cdelay(int i);


static void sdram_phy_sdram_command_p0(uint8_t cmd)
{
	sdram_dfii_pi0_command_write(cmd);
	sdram_dfii_pi0_command_issue_write(cmd);
}

static void sdram_phy_sdram_command_p1(uint8_t cmd)
{
	sdram_dfii_pi1_command_write(cmd);
	sdram_dfii_pi1_command_issue_write(cmd);
}

static void sdram_phy_sdram_command_p2(uint8_t cmd)
{
	sdram_dfii_pi2_command_write(cmd);
	sdram_dfii_pi2_command_issue_write(cmd);
}

static void sdram_phy_sdram_command_p3(uint8_t cmd)
{
	sdram_dfii_pi3_command_write(cmd);
	sdram_dfii_pi3_command_issue_write(cmd);
}


static void sdram_phy_sdram_init_sequence(void)
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
	sdram_phy_sdram_command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 6 */
	sdram_dfii_pi0_address_write(0x0);
	sdram_dfii_pi0_baddress_write(6);
	sdram_phy_sdram_command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 5 */
	sdram_dfii_pi0_address_write(0x0);
	sdram_dfii_pi0_baddress_write(5);
	sdram_phy_sdram_command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 4 */
	sdram_dfii_pi0_address_write(0x0);
	sdram_dfii_pi0_baddress_write(4);
	sdram_phy_sdram_command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 2, CWL=9 */
	sdram_dfii_pi0_address_write(0x200);
	sdram_dfii_pi0_baddress_write(2);
	sdram_phy_sdram_command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 1 */
	sdram_dfii_pi0_address_write(0x301);
	sdram_dfii_pi0_baddress_write(1);
	sdram_phy_sdram_command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);

	/* Load Mode Register 0, CL=11, BL=8 */
	sdram_dfii_pi0_address_write(0x110);
	sdram_dfii_pi0_baddress_write(0);
	sdram_phy_sdram_command_p0(DFII_COMMAND_RAS|DFII_COMMAND_CAS|DFII_COMMAND_WE|DFII_COMMAND_CS);
	cdelay(200);

	/* ZQ Calibration */
	sdram_dfii_pi0_address_write(0x400);
	sdram_dfii_pi0_baddress_write(0);
	sdram_phy_sdram_command_p0(DFII_COMMAND_WE|DFII_COMMAND_CS);
	cdelay(200);
}


static inline void sdram_phy_init_all(void)
{
	sdram_phy_sdram_init_sequence();
}


struct sdram_phy_t {
	uint8_t nphases;
	uint8_t pix_data_size;
	uint16_t ddrx_mr1;

	unsigned long pix_wrdata_addr[DFII_NPHASES_MAX];
	unsigned long pix_rddata_addr[DFII_NPHASES_MAX];

	void (* control_write)(uint8_t v);

	void (* pix_command_write[DFII_NPHASES_MAX])(uint8_t v);
	void (* pix_command_issue_write[DFII_NPHASES_MAX])(uint8_t v);

	void (* pix_address_write[DFII_NPHASES_MAX])(uint16_t v);
	void (* pird_address_write)(uint16_t v);
	void (* piwr_address_write)(uint16_t v);

	void (* pix_baddress_write[DFII_NPHASES_MAX])(uint8_t v);
	void (* pird_baddress_write)(uint8_t v);
	void (* piwr_baddress_write)(uint8_t v);

	void (* command_px[DFII_NPHASES_MAX])(uint8_t cmd);
	void (* command_prd)(uint8_t cmd);
	void (* command_pwr)(uint8_t cmd);

	void (* init)(void);
};

static const struct sdram_phy_t sdram_phys[] = {
	/* sdram */
	{
		4,
		CSR_SDRAM_DFII_PI0_WRDATA_SIZE,
		0x301,
		{
			CSR_SDRAM_DFII_PI0_WRDATA_ADDR,
			CSR_SDRAM_DFII_PI1_WRDATA_ADDR,
			CSR_SDRAM_DFII_PI2_WRDATA_ADDR,
			CSR_SDRAM_DFII_PI3_WRDATA_ADDR
		},
		{
			CSR_SDRAM_DFII_PI0_RDDATA_ADDR,
			CSR_SDRAM_DFII_PI1_RDDATA_ADDR,
			CSR_SDRAM_DFII_PI2_RDDATA_ADDR,
			CSR_SDRAM_DFII_PI3_RDDATA_ADDR
		},
		sdram_dfii_control_write,
		{
			sdram_dfii_pi0_command_write,
			sdram_dfii_pi1_command_write,
			sdram_dfii_pi2_command_write,
			sdram_dfii_pi3_command_write
		},
		{
			sdram_dfii_pi0_command_issue_write,
			sdram_dfii_pi1_command_issue_write,
			sdram_dfii_pi2_command_issue_write,
			sdram_dfii_pi3_command_issue_write
		},
		{
			sdram_dfii_pi0_address_write,
			sdram_dfii_pi1_address_write,
			sdram_dfii_pi2_address_write,
			sdram_dfii_pi3_address_write
		},
		sdram_dfii_pi1_address_write, /* rd */
		sdram_dfii_pi3_address_write, /* wr */
		{
			sdram_dfii_pi0_baddress_write,
			sdram_dfii_pi1_baddress_write,
			sdram_dfii_pi2_baddress_write,
			sdram_dfii_pi3_baddress_write
		},
		sdram_dfii_pi1_baddress_write, /* rd */
		sdram_dfii_pi3_baddress_write, /* wr */
		{
			sdram_phy_sdram_command_p0,
			sdram_phy_sdram_command_p1,
			sdram_phy_sdram_command_p2,
			sdram_phy_sdram_command_p3
		},
		sdram_phy_sdram_command_p1, /* rd */
		sdram_phy_sdram_command_p3, /* wr */
		sdram_phy_sdram_init_sequence
	}
};


/*** backward compatibility ***/

#ifndef SDRAM_PHY_DISABLE_BACKWARD_COMPATIBILITY

#define DFII_NPHASES 4

static inline __attribute__((always_inline)) void command_p0(uint8_t v) { sdram_phy_sdram_command_p0(v); }
static inline __attribute__((always_inline)) void command_p1(uint8_t v) { sdram_phy_sdram_command_p1(v); }
static inline __attribute__((always_inline)) void command_p2(uint8_t v) { sdram_phy_sdram_command_p2(v); }
static inline __attribute__((always_inline)) void command_p3(uint8_t v) { sdram_phy_sdram_command_p3(v); }
static inline __attribute__((always_inline)) void sdram_dfii_pird_address_write(uint16_t v) { sdram_dfii_pi1_address_write(v); }
static inline __attribute__((always_inline)) void sdram_dfii_piwr_address_write(uint16_t v) { sdram_dfii_pi3_address_write(v); }
static inline __attribute__((always_inline)) void sdram_dfii_pird_baddress_write(uint8_t v) { sdram_dfii_pi1_baddress_write(v); }
static inline __attribute__((always_inline)) void sdram_dfii_piwr_baddress_write(uint8_t v) { sdram_dfii_pi3_baddress_write(v); }
static inline __attribute__((always_inline)) void command_prd(uint8_t v) { sdram_phy_sdram_command_p1(v); }
static inline __attribute__((always_inline)) void command_pwr(uint8_t v) { sdram_phy_sdram_command_p3(v); }

#define DFII_PIX_DATA_SIZE CSR_SDRAM_DFII_PI0_WRDATA_SIZE

const unsigned long sdram_dfii_pix_wrdata_addr[DFII_NPHASES] = {
	CSR_SDRAM_DFII_PI0_WRDATA_ADDR,
	CSR_SDRAM_DFII_PI1_WRDATA_ADDR,
	CSR_SDRAM_DFII_PI2_WRDATA_ADDR,
	CSR_SDRAM_DFII_PI3_WRDATA_ADDR
};
const unsigned long sdram_dfii_pix_rddata_addr[DFII_NPHASES] = {
	CSR_SDRAM_DFII_PI0_RDDATA_ADDR,
	CSR_SDRAM_DFII_PI1_RDDATA_ADDR,
	CSR_SDRAM_DFII_PI2_RDDATA_ADDR,
	CSR_SDRAM_DFII_PI3_RDDATA_ADDR
};

#define DDRX_MR1 769

static inline __attribute__((always_inline)) void init_sequence(void) { sdram_phy_init_all(); }

#endif /* SDRAM_PHY_DISABLE_BACKWARD_COMPATIBILITY */

#endif /* __GENERATED_SDRAM_PHY_H */
