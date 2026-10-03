"""Fixed business and bill-header details."""

BILL_TITLE = "|| SHREE GAJANAN PRASANNA ||"
BUSINESS_NAME = "RAMESH RAMCHANDRA KASHID"
BUSINESS_SUBTITLE = "TATA ACE, PIAGGIO APE ON RENT"
BUSINESS_ADDRESS = "A/p. Kharpudi Bk., Tal. Khed, Dist. Pune - 410 501. Mob. 8855869548"
BANK_DETAILS = "A/c. No.: 060110110005977  IFSC Code: BKID0000601  PAN No.: EFOPK8546A"
BILL_FOOTER_MESSAGE = "Thank you !"
BILL_FOOTER_BUSINESS = "For RAMESH RAMCHANDRA KASHID"
STARTING_CHALLAN_NUMBER = 6002

# SQLite creates this database file automatically when it is first opened.
DATABASE_NAME = "driver_billing.db"

# Choose "full" for a designed bill, or "values" for pre-printed bill paper.
DEFAULT_PRINT_MODE = "full"

# Text positions for values-only printing, measured in millimetres from the
# top-left corner of an A5 portrait sheet. Adjust these for your bill book.
PREPRINTED_OFFSETS_MM = {
	"customer_name": {"x": 13, "y": 54},
	"challan_no": {"x": 119, "y": 54},
	"date": {"x": 119, "y": 61},
	"vehicle_no": {"x": 13, "y": 61},
	"rows": {
		"sr_no_x": 13,
		"description_x": 25,
		"amount_x": 119,
		"start_y": 79,
		"line_spacing": 7.5,
	},
	"balance": {"x": 119, "y": 162},
	"total": {"x": 119, "y": 170},
	"amount_words": {"x": 13, "y": 179},
}
