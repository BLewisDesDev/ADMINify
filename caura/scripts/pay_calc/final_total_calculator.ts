// File: FinalTotalCalculator.ts
// Script to calculate Final Total based on Initial Total + Error Shift Decisions

function main(workbook: ExcelScript.Workbook): void {
	console.log("=== FINAL TOTAL CALCULATOR ===");
	console.log(
		"Calculating Final Total = Initial Total + Sum(Error Shift Decisions)"
	);

	// Get the Staff Summary sheet
	const staffSummarySheet = workbook.getWorksheet("Staff Summary");
	if (!staffSummarySheet) {
		console.log(
			"ERROR: Staff Summary sheet not found. Please run the main pay automation script first."
		);
		return;
	}

	// Get the Error Shifts sheet
	const errorShiftsSheet = workbook.getWorksheet("Error Shifts");
	if (!errorShiftsSheet) {
		console.log(
			"ERROR: Error Shifts sheet not found. Please run the main pay automation script first."
		);
		return;
	}

	console.log("Found both Staff Summary and Error Shifts sheets");

	// Get data from Staff Summary sheet
	const staffSummaryRange = staffSummarySheet.getUsedRange();
	if (!staffSummaryRange) {
		console.log("ERROR: No data found in Staff Summary sheet");
		return;
	}

	const staffSummaryData = staffSummaryRange.getValues();
	const staffSummaryHeaders = staffSummaryData[0];

	// Find column indices in Staff Summary
	const staffColumnIndex = staffSummaryHeaders.findIndex(
		(header) => header && header.toString().toLowerCase().includes("staff")
	);
	const initialTotalColumnIndex = staffSummaryHeaders.findIndex(
		(header) =>
			header && header.toString().toLowerCase().includes("initial total")
	);
	const finalTotalColumnIndex = staffSummaryHeaders.findIndex(
		(header) =>
			header && header.toString().toLowerCase().includes("final total")
	);

	if (
		staffColumnIndex === -1 ||
		initialTotalColumnIndex === -1 ||
		finalTotalColumnIndex === -1
	) {
		console.log(
			"ERROR: Could not find required columns in Staff Summary sheet"
		);
		console.log(
			`Staff: ${staffColumnIndex}, Initial Total: ${initialTotalColumnIndex}, Final Total: ${finalTotalColumnIndex}`
		);
		return;
	}

	console.log(
		`Found columns - Staff: ${staffColumnIndex}, Initial Total: ${initialTotalColumnIndex}, Final Total: ${finalTotalColumnIndex}`
	);

	// Get data from Error Shifts sheet
	const errorShiftsRange = errorShiftsSheet.getUsedRange();
	if (!errorShiftsRange) {
		console.log(
			"No Error Shifts data found - all staff will have Final Total = Initial Total"
		);
	}

	let errorShiftsData: (string | number | boolean)[][] = [];
	let errorStaffColumnIndex = -1;
	let errorDecisionColumnIndex = -1;

	if (errorShiftsRange) {
		errorShiftsData = errorShiftsRange.getValues();
		const errorShiftsHeaders = errorShiftsData[0];

		// Find column indices in Error Shifts
		errorStaffColumnIndex = errorShiftsHeaders.findIndex(
			(header) => header && header.toString().toLowerCase().includes("staff")
		);
		errorDecisionColumnIndex = errorShiftsHeaders.findIndex(
			(header) => header && header.toString().toLowerCase().includes("decision")
		);

		if (errorStaffColumnIndex === -1 || errorDecisionColumnIndex === -1) {
			console.log(
				"ERROR: Could not find required columns in Error Shifts sheet"
			);
			console.log(
				`Staff: ${errorStaffColumnIndex}, Decision: ${errorDecisionColumnIndex}`
			);
			return;
		}

		console.log(
			`Error Shifts columns - Staff: ${errorStaffColumnIndex}, Decision: ${errorDecisionColumnIndex}`
		);
	}

	// Calculate decision totals for each staff member
	const staffDecisionTotals: { [staffName: string]: number } = {};

	if (errorShiftsData.length > 1) {
		// Skip header row (index 0)
		for (let i = 1; i < errorShiftsData.length; i++) {
			const row = errorShiftsData[i];
			const staffName = String(row[errorStaffColumnIndex] || "").trim();
			const decisionValue = row[errorDecisionColumnIndex];

			if (staffName) {
				// Initialize staff total if not exists
				if (!staffDecisionTotals[staffName]) {
					staffDecisionTotals[staffName] = 0;
				}

				// Add decision value if it's a valid number
				if (
					decisionValue !== null &&
					decisionValue !== undefined &&
					decisionValue !== ""
				) {
					const numericValue = Number(decisionValue);
					if (!isNaN(numericValue)) {
						staffDecisionTotals[staffName] += numericValue;
					}
				}
			}
		}
	}

	console.log("Decision totals calculated:");
	for (const staffName in staffDecisionTotals) {
		console.log(`  ${staffName}: ${staffDecisionTotals[staffName]}`);
	}

	// Update Final Total column in Staff Summary
	let updatedCount = 0;
	const calculationResults: string[] = [];

	// Skip header row (index 0) and totals row (last row)
	for (let i = 1; i < staffSummaryData.length - 1; i++) {
		const row = staffSummaryData[i];
		const staffName = String(row[staffColumnIndex] || "").trim();
		const initialTotal = Number(row[initialTotalColumnIndex]) || 0;

		// Get decision total for this staff member (default to 0 if no decisions)
		const decisionTotal = staffDecisionTotals[staffName] || 0;

		// Calculate Final Total = Initial Total + Decision Total
		const finalTotal = Math.round((initialTotal + decisionTotal) * 100) / 100;

		// Update the Final Total cell
		const cellAddress = `${String.fromCharCode(65 + finalTotalColumnIndex)}${
			i + 1
		}`;
		const finalTotalCell = staffSummarySheet.getRange(cellAddress);
		finalTotalCell.setValue(finalTotal);

		calculationResults.push(
			`${staffName}: ${initialTotal} + ${decisionTotal} = ${finalTotal}`
		);
		updatedCount++;
	}

	// Update totals row if it exists
	const totalsRowIndex = staffSummaryData.length - 1;
	if (
		totalsRowIndex > 0 &&
		String(staffSummaryData[totalsRowIndex][0]).includes("TOTAL")
	) {
		// Calculate total of all final totals
		let grandFinalTotal = 0;
		for (let i = 1; i < staffSummaryData.length - 1; i++) {
			const staffName = String(
				staffSummaryData[i][staffColumnIndex] || ""
			).trim();
			const initialTotal =
				Number(staffSummaryData[i][initialTotalColumnIndex]) || 0;
			const decisionTotal = staffDecisionTotals[staffName] || 0;
			grandFinalTotal += initialTotal + decisionTotal;
		}

		// Update the totals row Final Total cell
		const totalsCellAddress = `${String.fromCharCode(
			65 + finalTotalColumnIndex
		)}${totalsRowIndex + 1}`;
		const totalsFinalCell = staffSummarySheet.getRange(totalsCellAddress);
		totalsFinalCell.setValue(Math.round(grandFinalTotal * 100) / 100);

		console.log(
			`Updated totals row with grand final total: ${
				Math.round(grandFinalTotal * 100) / 100
			}`
		);
	}

	// Output calculation results
	console.log("\nFinal Total Calculations:");
	console.log(calculationResults.join("\n"));

	console.log(`\n=== CALCULATION COMPLETE ===`);
	console.log(`Updated ${updatedCount} staff members with final totals`);
	console.log(
		"Formula used: Final Total = Initial Total + Sum(Error Shift Decisions)"
	);

	if (Object.keys(staffDecisionTotals).length === 0) {
		console.log(
			"Note: No decision values found - all Final Totals equal Initial Totals"
		);
	} else {
		console.log(
			`Note: Found decision values for ${
				Object.keys(staffDecisionTotals).length
			} staff members`
		);
	}
}
