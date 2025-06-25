// File: PayAutomationScript_Updated.ts
// Enhanced Pay Automation with Modified Error Shifts Sheet Layout and Dynamic Deductions

// ===== CONFIGURATION =====
const CONFIG = {
	workPercentageThresholds: { min: 10 }, // Only minimum threshold now
	clockTimeDifferenceThreshold: 30,
	debugMode: true,
	// maxTestRows will be set dynamically based on actual data

	// Hardcoded column mappings based on your CSV structure
	columns: {
		shiftId: 0, // A: "Shift ID"
		clientName: 1, // B: "Name"
		address: 2, // C: "Address"
		staff: 3, // D: "Staff"
		staffId: 4, // E: "Staff ID"
		startDateTime: 5, // F: "Start Date Time"
		endDateTime: 6, // G: "End Date Time"
		hours: 7, // H: "Hours"
		mileage: 8, // I: "Mileage" (ignore)
		expense: 9, // J: "Expense" (ignore)
		absentShift: 10, // K: "Absent Shift" (ignore)
		status: 11, // L: "Shift Status"
		cancelledReason: 12, // M: "Cancelled Reason"
		clockinDateTime: 13, // N: "Clockin Date Time"
		clockoutDateTime: 14, // O: "Clockout Date Time"
		shiftType: 15, // P: "Shift Type"
		url: 16, // Q: "URL"
		note: 17, // R: "Note"
	},
};

// ===== DOMAIN MODELS =====
enum ErrorType {
	MISSED_CLOCK_IN = "MISSED CLOCK IN",
	MISSED_CLOCK_OUT = "MISSED CLOCK OUT",
	MISSED_BOTH = "MISSED CLOCK IN&OUT",
	WORKED_TIME_UNDER_10 = "WORKED TIME < 10%",
	REBOOK_SHIFT = "REBOOK SHIFT",
	CANCELLED_SHIFT = "CANCELLED SHIFT",
	PENDING_SHIFT = "PENDING SHIFT",
}

interface ShiftData {
	shiftId: string;
	staff: string;
	client: string;
	date: Date;
	bookedTime: number; // hours from "Hours" column
	workedTime: number; // calculated from clockin/out
	errorTypes: ErrorType[]; // Array to support multiple errors
	hasNote: boolean;
	url: string;
}

// ===== SIMPLE PARSER FUNCTIONS =====
function parseDate(value: string | number | boolean): Date {
	if (!value) return new Date();

	if (typeof value === "number") {
		// Excel date serial number
		return new Date((value - 25569) * 86400 * 1000);
	}

	let dateStr = String(value).trim();

	// Handle the timezone format: "2025-06-16 08:00:00 +1000"
	if (dateStr.includes("+") || dateStr.includes("-")) {
		// Remove timezone completely for simpler parsing
		dateStr = dateStr.replace(/\s*[+-]\d{4}$/, "");

		// Also handle the colon format "+10:00" if present
		dateStr = dateStr.replace(/\s*[+-]\d{2}:\d{2}$/, "");
	}

	// Clean up any extra spaces
	dateStr = dateStr.trim();

	return new Date(dateStr);
}

function calculateHours(
	startValue: string | number | boolean,
	endValue: string | number | boolean
): number {
	if (!startValue || !endValue) return 0;

	const startDate = parseDate(startValue);
	const endDate = parseDate(endValue);

	// Check if dates are valid
	if (isNaN(startDate.getTime()) || isNaN(endDate.getTime())) {
		return 0;
	}

	const diffMs = Math.abs(endDate.getTime() - startDate.getTime());
	return diffMs / (1000 * 60 * 60); // Convert to hours
}

function hasValidTimeValue(value: string | number | boolean): boolean {
	if (!value) return false;
	const str = String(value).trim();

	// Check for empty, null, or zero values
	if (str === "" || str.toLowerCase() === "null" || str === "0") {
		return false;
	}

	// Try to parse as date to ensure it's valid
	const testDate = parseDate(value);
	return !isNaN(testDate.getTime());
}

function determineErrorTypes(
	row: (string | number | boolean)[],
	bookedTime: number,
	workedTime: number
): ErrorType[] {
	const cols = CONFIG.columns;
	const errors: ErrorType[] = [];

	// Check shift type first
	const shiftType = String(row[cols.shiftType] || "")
		.toLowerCase()
		.trim();
	if (shiftType === "rebook") {
		errors.push(ErrorType.REBOOK_SHIFT);
		return errors;
	}

	// Check status for cancelled/pending
	const status = String(row[cols.status] || "")
		.toLowerCase()
		.trim();
	if (status === "cancelled") {
		errors.push(ErrorType.CANCELLED_SHIFT);
		return errors;
	}
	if (status === "pending") {
		errors.push(ErrorType.PENDING_SHIFT);
		return errors;
	}

	// Check for missing clock times
	const hasClockIn = hasValidTimeValue(row[cols.clockinDateTime]);
	const hasClockOut = hasValidTimeValue(row[cols.clockoutDateTime]);

	if (!hasClockIn && !hasClockOut) {
		errors.push(ErrorType.MISSED_BOTH);
	} else if (!hasClockIn) {
		errors.push(ErrorType.MISSED_CLOCK_IN);
	} else if (!hasClockOut) {
		errors.push(ErrorType.MISSED_CLOCK_OUT);
	}

	// Check work percentage anomalies (only if we have both times)
	if (bookedTime > 0 && workedTime > 0) {
		const percentage = (workedTime / bookedTime) * 100;

		if (percentage < CONFIG.workPercentageThresholds.min) {
			errors.push(ErrorType.WORKED_TIME_UNDER_10);
		}
	}

	return errors;
}

function parseShiftRow(
	row: (string | number | boolean)[],
	rowIndex: number
): ShiftData | null {
	const cols = CONFIG.columns;

	// Extract basic data
	const shiftId = String(row[cols.shiftId] || "").trim();
	const staff = String(row[cols.staff] || "").trim();
	const client = String(row[cols.clientName] || "").trim();

	if (!staff || !client) {
		return null; // Skip rows without required data
	}

	// Get times
	const bookedTime = Number(row[cols.hours]) || 0; // Use the "Hours" column directly
	const workedTime = calculateHours(
		row[cols.clockinDateTime],
		row[cols.clockoutDateTime]
	);

	// Determine errors (now returns array)
	const errorTypes = determineErrorTypes(row, bookedTime, workedTime);

	// Check for notes
	const noteValue = row[cols.note];
	const hasNote = noteValue ? String(noteValue).trim() !== "" : false;

	// Build shift object
	const shift: ShiftData = {
		shiftId: shiftId,
		staff: staff,
		client: client,
		date: parseDate(row[cols.startDateTime]),
		bookedTime: bookedTime,
		workedTime: workedTime,
		errorTypes: errorTypes, // Now an array
		hasNote: hasNote,
		url: String(row[cols.url] || ""),
	};

	return shift;
}

// ===== SORTING AND FORMATTING HELPER =====
function sortAndFormatMainWorksheet(workbook: ExcelScript.Workbook): boolean {
	console.log("=== SORTING AND FORMATTING MAIN WORKSHEET ===");

	// Find worksheet that starts with "Activity_Raw_Export_Staff"
	const worksheets = workbook.getWorksheets();
	let worksheet: ExcelScript.Worksheet | undefined;

	for (const ws of worksheets) {
		if (ws.getName().startsWith("Activity_Raw_Export_Staff")) {
			worksheet = ws;
			break;
		}
	}

	if (!worksheet) {
		console.log(
			"ERROR: Could not find worksheet starting with 'Activity_Raw_Export_Staff'"
		);
		console.log("Available worksheets:");
		for (const ws of worksheets) {
			console.log(`  - ${ws.getName()}`);
		}
		return false;
	}

	console.log(`Found worksheet: ${worksheet.getName()}`);

	const usedRange = worksheet.getUsedRange();
	if (!usedRange) {
		console.log("ERROR: No data found in worksheet");
		return false;
	}

	console.log(
		`Data range: ${usedRange.getRowCount()} rows x ${usedRange.getColumnCount()} columns`
	);

	// Step 1: Normalize column widths first
	console.log("Step 1: Normalizing column widths...");
	usedRange.getFormat().autofitColumns();
	console.log("Column widths normalized");

	// Step 2: Sort by Staff column only (Column D = index 3)
	console.log("Step 2: Sorting by Staff column...");

	// Get data range excluding header
	const dataRange = worksheet.getRange(
		`A2:${String.fromCharCode(
			65 + usedRange.getColumnCount() - 1
		)}${usedRange.getRowCount()}`
	);

	const sortField: ExcelScript.SortField[] = [
		{
			key: 3, // Staff column (D = index 3)
			ascending: true,
		},
	];

	dataRange.getSort().apply(sortField);
	console.log("Worksheet sorted by Staff column successfully");

	return true;
}

// ===== MAIN PROCESSING FUNCTION =====
function processShiftData(workbook: ExcelScript.Workbook): ShiftData[] {
	// Find worksheet that starts with "Activity_Raw_Export_Staff"
	const worksheets = workbook.getWorksheets();
	let worksheet: ExcelScript.Worksheet | undefined;

	for (const ws of worksheets) {
		if (ws.getName().startsWith("Activity_Raw_Export_Staff")) {
			worksheet = ws;
			break;
		}
	}

	if (!worksheet) {
		console.log(
			"ERROR: Could not find worksheet starting with 'Activity_Raw_Export_Staff'"
		);
		return [];
	}

	console.log(`\n=== PROCESSING SHIFT DATA ===`);
	console.log(`Using worksheet: ${worksheet.getName()}`);

	const usedRange = worksheet.getUsedRange();

	if (!usedRange) {
		console.log("No data found in worksheet");
		return [];
	}

	const values = usedRange.getValues();
	if (values.length < 2) {
		console.log("Need at least 2 rows (header + data)");
		return [];
	}

	const headerRow = values[0];
	const totalDataRows = values.length - 1; // Subtract 1 for header row
	console.log(`Found ${headerRow.length} columns in header`);
	console.log(`Processing all ${totalDataRows} data rows dynamically`);

	const shifts: ShiftData[] = [];
	const parseResults: string[] = [];

	// Process all rows (skip header) - dynamic based on actual data
	for (let i = 1; i < values.length; i++) {
		const row = values[i];
		const shift = parseShiftRow(row, i);

		if (shift) {
			shifts.push(shift);

			const errorText =
				shift.errorTypes.length > 0 ? shift.errorTypes.join(", ") : "None";
			const workPercent =
				shift.bookedTime > 0 && !isNaN(shift.workedTime)
					? ((shift.workedTime / shift.bookedTime) * 100).toFixed(1) + "%"
					: "N/A";
			const workedDisplay = isNaN(shift.workedTime)
				? "0.00"
				: shift.workedTime.toFixed(2);

			parseResults.push(
				`Row ${i}: ${shift.staff} | ${shift.client} | ` +
					`${shift.bookedTime}h booked | ${workedDisplay}h worked (${workPercent}) | ` +
					`Errors: ${errorText}`
			);
		} else {
			parseResults.push(`Row ${i}: ✗ Failed to parse (missing staff/client)`);
		}
	}

	// Output all results at once (no loop console.log)
	console.log("\n=== PARSED SHIFTS ===");
	console.log(parseResults.join("\n"));

	return shifts;
}

// ===== UPDATED ERROR SHIFTS SPREADSHEET GENERATOR =====
function createErrorShiftsSheet(
	workbook: ExcelScript.Workbook,
	shifts: ShiftData[]
): void {
	// Filter only shifts with errors
	const errorShifts = shifts.filter((shift) => shift.errorTypes.length > 0);

	if (errorShifts.length === 0) {
		console.log("No error shifts found - no sheet created");
		return;
	}

	// Delete existing sheet if it exists to prevent issues
	let errorSheet = workbook.getWorksheet("Error Shifts");
	if (errorSheet) {
		console.log("Deleting existing Error Shifts sheet to prevent conflicts");
		errorSheet.delete();
	}

	// Create new sheet
	errorSheet = workbook.addWorksheet("Error Shifts");

	// Updated headers - removed Client, Shift ID, Worked Hours, added Has Notes
	const headers = [
		"Staff",
		"Booked Hours",
		"Work %",
		"Error Type",
		"URL",
		"Has Notes",
		"Decision",
	];

	// Set headers
	const headerRange = errorSheet.getRange("A1:G1");
	headerRange.setValues([headers]);

	// Format headers
	headerRange.getFormat().getFont().setBold(true);
	headerRange.getFormat().getFill().setColor("#4CAF50"); // Green background
	headerRange.getFormat().getFont().setColor("#FFFFFF"); // White text

	// Prepare data rows
	const dataRows: (string | number | boolean)[][] = [];

	for (const shift of errorShifts) {
		const workPercentage =
			shift.bookedTime > 0 && !isNaN(shift.workedTime)
				? Math.round((shift.workedTime / shift.bookedTime) * 100)
				: 0;

		const errorTypesText = shift.errorTypes.join(", "); // Join multiple errors

		dataRows.push([
			shift.staff,
			shift.bookedTime,
			workPercentage,
			errorTypesText,
			shift.url,
			shift.hasNote ? "Yes" : "No", // Has Notes column
			"", // Empty decision column for user input
		]);
	}

	// Set data
	if (dataRows.length > 0) {
		const dataRange = errorSheet.getRange(`A2:G${dataRows.length + 1}`);
		dataRange.setValues(dataRows);

		// Format work percentage column (column C) - use simpler string format
		for (let i = 0; i < dataRows.length; i++) {
			const percentCell = errorSheet.getRange(`C${i + 2}`);
			const percentValue = dataRows[i][2] as number;
			percentCell.setValue(`${percentValue}%`); // Set as text with % symbol
		}

		// Color code ONLY the Error Type column (column D) based on FIRST error type
		for (let i = 0; i < dataRows.length; i++) {
			const rowNum = i + 2;
			const errorTypesText = dataRows[i][3] as string;
			const errorTypesArray = errorTypesText.split(", ");
			const firstErrorType = errorTypesArray[0]; // Get FIRST error for coloring
			const errorTypeCell = errorSheet.getRange(`D${rowNum}`); // Only color the Error Type column

			// Color based on first error type with specific colors for cancelled/pending
			if (firstErrorType.includes("CANCELLED")) {
				errorTypeCell.getFormat().getFill().setColor("#F2A1A1"); // 50% lighter red for cancelled
			} else if (firstErrorType.includes("PENDING")) {
				errorTypeCell.getFormat().getFill().setColor("#FFD280"); // 50% lighter orange for pending
			} else if (firstErrorType.includes("MISSED CLOCK IN&OUT")) {
				errorTypeCell.getFormat().getFill().setColor("#A1CCF0"); // 50% lighter darkest blue for both missing
			} else if (firstErrorType.includes("MISSED CLOCK OUT")) {
				errorTypeCell.getFormat().getFill().setColor("#C8E6FA"); // 50% lighter mid blue for clock out
			} else if (firstErrorType.includes("MISSED CLOCK IN")) {
				errorTypeCell.getFormat().getFill().setColor("#DFF1FC"); // 50% lighter lightest blue for clock in
			} else if (
				firstErrorType.includes("WORKED TIME") ||
				firstErrorType.includes("REBOOK")
			) {
				errorTypeCell.getFormat().getFill().setColor("#CFBDF5"); // 50% lighter purple for time anomalies
			}
		}
	}

	// Auto-fit columns with normalized widths
	const usedRange = errorSheet.getUsedRange();
	if (usedRange) {
		usedRange.getFormat().autofitColumns();
	}

	// Freeze header row
	errorSheet.getFreezePanes().freezeRows(1);

	console.log(
		`Created "Error Shifts" sheet with ${errorShifts.length} problematic shifts`
	);
}

// ===== STAFF SUMMARY SPREADSHEET GENERATOR WITH DYNAMIC DEDUCTIONS =====
function createStaffSummarySheet(
	workbook: ExcelScript.Workbook,
	shifts: ShiftData[]
): void {
	if (shifts.length === 0) {
		console.log("No shifts to summarize");
		return;
	}

	// Delete existing sheet if it exists to prevent issues
	let summarySheet = workbook.getWorksheet("Staff Summary");
	if (summarySheet) {
		console.log("Deleting existing Staff Summary sheet to prevent conflicts");
		summarySheet.delete();
	}

	// Create new sheet
	summarySheet = workbook.addWorksheet("Staff Summary");

	// Group shifts by staff
	const staffGroups: { [key: string]: ShiftData[] } = {};

	for (const shift of shifts) {
		if (!staffGroups[shift.staff]) {
			staffGroups[shift.staff] = [];
		}
		staffGroups[shift.staff].push(shift);
	}

	// Create headers - updated layout with Status column
	const headers = [
		"Staff",
		"Status",
		"Booked Hours",
		"Cancelled",
		"Pending",
		"Missing Clocks",
		"<10% Worked",
		"Initial Total",
		"Final Total",
	];

	// Set headers
	const headerRange = summarySheet.getRange("A1:I1");
	headerRange.setValues([headers]);

	// Format headers
	headerRange.getFormat().getFont().setBold(true);
	headerRange.getFormat().getFill().setColor("#4CAF50"); // Green background
	headerRange.getFormat().getFont().setColor("#FFFFFF"); // White text

	// Prepare summary data
	const summaryData: (string | number)[][] = [];
	let totalBookedHours = 0;
	let totalCancelled = 0;
	let totalPending = 0;
	let totalMissingClocks = 0;
	let totalUnder10Percent = 0;
	let totalErrorShiftDeductions = 0; // Track total deductions across all staff

	for (const staffName in staffGroups) {
		const staffShifts = staffGroups[staffName];

		let bookedHours = 0;
		let cancelledCount = 0;
		let pendingCount = 0;
		let missingClocksCount = 0;
		let under10PercentCount = 0;
		let staffErrorShiftDeductions = 0; // Track actual booked hours of error shifts for this staff

		for (const shift of staffShifts) {
			bookedHours += shift.bookedTime;

			// Count specific error types AND track their booked hours for deductions
			for (const errorType of shift.errorTypes) {
				if (errorType === ErrorType.CANCELLED_SHIFT) {
					cancelledCount++;
					staffErrorShiftDeductions += shift.bookedTime; // Deduct actual booked hours
				} else if (errorType === ErrorType.PENDING_SHIFT) {
					pendingCount++;
					staffErrorShiftDeductions += shift.bookedTime; // Deduct actual booked hours
				} else if (
					errorType === ErrorType.MISSED_CLOCK_IN ||
					errorType === ErrorType.MISSED_CLOCK_OUT ||
					errorType === ErrorType.MISSED_BOTH
				) {
					missingClocksCount++;
					staffErrorShiftDeductions += shift.bookedTime; // Deduct actual booked hours
				} else if (errorType === ErrorType.WORKED_TIME_UNDER_10) {
					under10PercentCount++;
					staffErrorShiftDeductions += shift.bookedTime; // Deduct actual booked hours
				}
			}
		}

		// Calculate Initial Total using dynamic deductions based on actual booked hours
		const initialTotal =
			Math.round((bookedHours - staffErrorShiftDeductions) * 100) / 100;

		// Status is GOOD if all error counts are 0
		const staffStatus =
			cancelledCount === 0 &&
			pendingCount === 0 &&
			missingClocksCount === 0 &&
			under10PercentCount === 0
				? "GOOD"
				: "CAUTION";

		summaryData.push([
			staffName,
			staffStatus,
			Math.round(bookedHours * 100) / 100,
			cancelledCount,
			pendingCount,
			missingClocksCount,
			under10PercentCount,
			initialTotal,
			"", // Empty Final Total column
		]);

		// Add to totals
		totalBookedHours += bookedHours;
		totalCancelled += cancelledCount;
		totalPending += pendingCount;
		totalMissingClocks += missingClocksCount;
		totalUnder10Percent += under10PercentCount;
		totalErrorShiftDeductions += staffErrorShiftDeductions; // Add this staff's error shift deductions to grand total
	}

	// Set summary data
	if (summaryData.length > 0) {
		const dataRange = summarySheet.getRange(`A2:I${summaryData.length + 1}`);
		dataRange.setValues(summaryData);

		// Color code Status column (column B)
		for (let i = 0; i < summaryData.length; i++) {
			const rowNum = i + 2;
			const status = summaryData[i][1] as string;
			const statusCell = summarySheet.getRange(`B${rowNum}`);

			if (status === "GOOD") {
				statusCell.getFormat().getFill().setColor("#90EE90"); // Light green
				statusCell.getFormat().getFont().setColor("#006400"); // Dark green text
			} else {
				statusCell.getFormat().getFill().setColor("#FFA500"); // Orange
				statusCell.getFormat().getFont().setColor("#8B4513"); // Dark brown text
			}
		}

		// Style Initial Total column (column H) - light background, no bold
		for (let i = 0; i < summaryData.length; i++) {
			const initialTotalCell = summarySheet.getRange(`H${i + 2}`);
			initialTotalCell.getFormat().getFill().setColor("#F0F8FF"); // Light blue background
			initialTotalCell.getFormat().getFont().setBold(false);
		}

		// Style Final Total column (column I) - darker background, bold text, but leave empty
		for (let i = 0; i < summaryData.length; i++) {
			const finalTotalCell = summarySheet.getRange(`I${i + 2}`);
			finalTotalCell.getFormat().getFill().setColor("#E6F3FF"); // Slightly darker blue background
			finalTotalCell.getFormat().getFont().setBold(true);
			finalTotalCell.getFormat().getFont().setColor("#2E86AB"); // Dark blue text
		}

		// Add totals row
		const totalRow = summaryData.length + 2;
		summarySheet.getRange(`A${totalRow}`).setValue("TOTALS:");
		summarySheet.getRange(`A${totalRow}`).getFormat().getFont().setBold(true);

		// Calculate totals row Initial Total using actual error shift deductions
		const totalInitialTotal =
			Math.round((totalBookedHours - totalErrorShiftDeductions) * 100) / 100;

		// Count GOOD vs CAUTION status
		const totalGoodCount = summaryData.filter(
			(row) => row[1] === "GOOD"
		).length;
		const totalCautionCount = summaryData.filter(
			(row) => row[1] === "CAUTION"
		).length;

		summarySheet.getRange(`B${totalRow}:I${totalRow}`).setValues([
			[
				`${totalGoodCount} Good, ${totalCautionCount} Caution`,
				Math.round(totalBookedHours * 100) / 100,
				totalCancelled,
				totalPending,
				totalMissingClocks,
				totalUnder10Percent,
				totalInitialTotal,
				"", // Empty Final Total
			],
		]);

		// Format totals row
		const totalsRange = summarySheet.getRange(`A${totalRow}:I${totalRow}`);
		totalsRange.getFormat().getFont().setBold(true);
		totalsRange.getFormat().getFill().setColor("#E0E0E0"); // Light gray background

		// Special formatting for totals Initial Total
		const totalsInitialCell = summarySheet.getRange(`H${totalRow}`);
		totalsInitialCell.getFormat().getFill().setColor("#D6EAF8"); // Slightly darker than individual cells

		const totalsFinalCell = summarySheet.getRange(`I${totalRow}`);
		totalsFinalCell.getFormat().getFill().setColor("#AED6F1"); // Even darker blue for final total
		totalsFinalCell.getFormat().getFont().setColor("#1B4F72"); // Very dark blue text
	}

	// Auto-fit columns with normalized widths
	const usedRange = summarySheet.getUsedRange();
	if (usedRange) {
		usedRange.getFormat().autofitColumns();
	}

	// Freeze header row
	summarySheet.getFreezePanes().freezeRows(1);

	console.log(
		`Created "Staff Summary" sheet with ${summaryData.length} staff members`
	);
}

// ===== MAIN ENTRY POINT =====
function main(workbook: ExcelScript.Workbook): void {
	console.log("=== PAY AUTOMATION SCRIPT - PRODUCTION VERSION ===");
	console.log(
		"Testing thesis: Sort first sheet properly, then process sequentially"
	);
	console.log(
		"Hypothesis: Secondary sheets will inherit sorting from main data processing\n"
	);

	// Step 1: Sort and format the main worksheet FIRST
	const sortSuccess = sortAndFormatMainWorksheet(workbook);
	if (!sortSuccess) {
		console.log("FAILED: Could not sort main worksheet. Stopping execution.");
		return;
	}

	// Step 2: Process the shift data (from now-sorted worksheet)
	const shifts = processShiftData(workbook);

	if (shifts.length === 0) {
		console.log("No valid shifts found to process");
		return;
	}

	console.log(`\n=== DATA PROCESSING COMPLETE ===`);
	console.log(`Successfully parsed ${shifts.length} shifts from sorted data`);

	// Step 3: Create secondary sheets (should inherit sort order)
	console.log(`\n=== CREATING SECONDARY SHEETS ===`);
	console.log(
		"Testing if Error Shifts and Staff Summary inherit sort order..."
	);

	createErrorShiftsSheet(workbook, shifts);
	createStaffSummarySheet(workbook, shifts);

	// Quick summary to console
	const errorShifts = shifts.filter((shift) => shift.errorTypes.length > 0);
	const multipleErrorShifts = shifts.filter(
		(shift) => shift.errorTypes.length > 1
	);
	const shiftsWithNotes = shifts.filter((shift) => shift.hasNote);

	console.log(`\n=== THESIS TEST RESULTS ===`);
	console.log(`- Main worksheet: Sorted by Staff (${sortSuccess ? "✓" : "✗"})`);
	console.log(
		`- Error Shifts created: ${errorShifts.length} shifts (should be in staff order)`
	);
	console.log(
		`- Staff Summary created: ${
			Object.keys(
				shifts.reduce((groups, shift) => {
					groups[shift.staff] = true;
					return groups;
				}, {} as { [key: string]: boolean })
			).length
		} staff (should be in staff order)`
	);
	console.log(`\n=== SUMMARY ===`);
	console.log(`- Total shifts processed: ${shifts.length}`);
	console.log(`- Error shifts found: ${errorShifts.length}`);
	console.log(`- Shifts with multiple errors: ${multipleErrorShifts.length}`);
	console.log(`- Shifts with notes: ${shiftsWithNotes.length}`);
	console.log(`\n=== FEATURES ===`);
	console.log(`- Main worksheet: Normalized columns + sorted by Staff only`);
	console.log(`- Dynamic deduction calculator: Uses actual booked hours`);
	console.log(
		`- Sequential processing: Secondary sheets inherit main sort order`
	);
	console.log(`\nERROR SHIFTS SHEET LAYOUT:`);
	console.log(
		`- Columns: Staff | Booked Hours | Work % | Error Type | URL | Has Notes | Decision`
	);
	console.log(`\nCOLOR CODING:`);
	console.log(`- Red: Cancelled shifts | Orange: Pending shifts`);
	console.log(
		`- Light Orange: Missing clock times | Light Purple: Time anomalies & rebook shifts`
	);

	console.log("\n=== THESIS TEST COMPLETE ===");
	console.log(
		"Check if Error Shifts and Staff Summary sheets are sorted by Staff!"
	);
	console.log(
		"If YES, thesis confirmed: Sequential processing maintains sort order"
	);
	console.log(
		"If NO, thesis disproven: Additional sorting needed on secondary sheets"
	);
}
