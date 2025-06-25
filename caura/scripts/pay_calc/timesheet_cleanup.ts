// File: SheetCleanup.ts
// Simple script to delete Error Shifts and Staff Summary sheets

function main(workbook: ExcelScript.Workbook): void {
	console.log("=== SHEET CLEANUP SCRIPT ===");
	console.log("Deleting Error Shifts and Staff Summary sheets if they exist");

	// Delete Error Shifts sheet
	const errorShiftsSheet = workbook.getWorksheet("Error Shifts");
	if (errorShiftsSheet) {
		errorShiftsSheet.delete();
		console.log("✓ Deleted: Error Shifts sheet");
	} else {
		console.log("- Error Shifts sheet not found (already clean)");
	}

	// Delete Staff Summary sheet
	const staffSummarySheet = workbook.getWorksheet("Staff Summary");
	if (staffSummarySheet) {
		staffSummarySheet.delete();
		console.log("✓ Deleted: Staff Summary sheet");
	} else {
		console.log("- Staff Summary sheet not found (already clean)");
	}

	console.log("=== CLEANUP COMPLETE ===");
	console.log("Ready to run the main pay automation script");
}
