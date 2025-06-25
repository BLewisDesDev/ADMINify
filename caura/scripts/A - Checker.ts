/**
 * SCHEDULE A CHECKER - Excel Office Script
 *
 * PURPOSE:
 * This script validates Schedule A entries from your CRM against eligible roster members.
 * It identifies mismatches and highlights them for easy review and correction.
 *
 * REQUIRED SHEETS:
 * 1. "Roster" sheet with columns: FirstName, LastName, Roster
 * 2. "ActivityReport" sheet with column: Schedule A
 *
 * FILTERING LOGIC:
 * Only roster members with these "Roster" column values are considered for matching:
 * - Schedule A
 * - Schedule A Monthly
 * - Weekly
 * - TriWeekly
 * (This filtering significantly improves performance by reducing comparison dataset)
 *
 * MATCHING PROCESS:
 * 1. Cleans names by removing parenthetical comments like "(John Smith)"
 * 2. Normalizes names by removing spaces and special characters, converting to lowercase
 * 3. Performs exact matching first (fast O(1) lookup)
 * 4. Uses fuzzy matching (85% similarity threshold) for remaining unmatched entries
 * 5. Processes in batches to optimize memory usage and prevent timeouts
 *
 * VISUAL RESULTS:
 * - UNMATCHED Schedule A entries (ActivityReport): Highlighted in LIGHT PINK background
 * - MATCHED roster entries (Roster sheet): Text color changed to RED in "Roster" column
 * - UNMATCHED roster entries: Text remains BLACK (no change)
 *
 * PERFORMANCE:
 * Optimized for thousands of records using:
 * - Dataset filtering (only Schedule A eligible entries)
 * - Two-pass matching (exact then fuzzy)
 * - Early termination algorithms
 * - Memory-efficient string comparison
 *
 * CONSOLE OUTPUT:
 * Provides detailed statistics including:
 * - Number of eligible roster entries found
 * - Number of Schedule A entries to match
 * - Count of exact vs fuzzy matches
 * - Summary of highlighting actions performed
 */
function main(workbook: ExcelScript.Workbook): void {
	// Disable automatic calculation for better performance
	const originalCalculationMode: ExcelScript.CalculationMode = workbook
		.getApplication()
		.getCalculationMode();
	workbook
		.getApplication()
		.setCalculationMode(ExcelScript.CalculationMode.manual);

	try {
		// Access both sheets
		const rosterSheet: ExcelScript.Worksheet | undefined =
			workbook.getWorksheet("Roster");
		const activitySheet: ExcelScript.Worksheet | undefined =
			workbook.getWorksheet("ActivityReport");

		if (!rosterSheet || !activitySheet) {
			console.log("Could not find one or both required sheets!");
			return;
		}

		// Step 1: Process Roster sheet - Filter by Schedule A criteria and get names
		console.log("=== DIAGNOSTIC INFO ===");
		console.log("Roster sheet found:", !!rosterSheet);

		// Instead of getUsedRange(), let's try a more targeted approach
		// First, let's see what's in the first few rows to find our headers
		const headerRange: ExcelScript.Range = rosterSheet.getRange("A1:Z10"); // Check first 10 rows, 26 columns
		const headerValues: (string | number | boolean)[][] =
			headerRange.getValues();

		console.log("Header range values retrieved successfully:", !!headerValues);
		console.log("First few rows:", headerValues.slice(0, 3));

		// Find the actual header row (look for our expected columns)
		let headerRowIndex: number = -1;
		let rosterHeaderRow: (string | number | boolean)[] = [];

		for (let i = 0; i < headerValues.length; i++) {
			const row = headerValues[i];
			if (
				row.some((cell) => cell && cell.toString().includes("FirstName")) ||
				row.some((cell) => cell && cell.toString().includes("LastName")) ||
				row.some((cell) => cell && cell.toString().includes("Roster"))
			) {
				headerRowIndex = i;
				rosterHeaderRow = row;
				console.log(
					`Found headers in row ${i + 1}:`,
					row.filter((cell) => cell && cell.toString().trim())
				);
				break;
			}
		}

		if (headerRowIndex === -1) {
			console.log("Could not find header row with expected columns!");
			console.log("First 5 rows content:", headerValues.slice(0, 5));
			return;
		}

		// Find column indices
		const firstNameColIndex: number = rosterHeaderRow.findIndex(
			(col) => col && col.toString().trim() === "FirstName"
		);
		const lastNameColIndex: number = rosterHeaderRow.findIndex(
			(col) => col && col.toString().trim() === "LastName"
		);
		const rosterColIndex: number = rosterHeaderRow.findIndex(
			(col) => col && col.toString().trim() === "Roster"
		);

		console.log("Column indices found:", {
			firstName: firstNameColIndex,
			lastName: lastNameColIndex,
			roster: rosterColIndex,
		});

		if (
			firstNameColIndex === -1 ||
			lastNameColIndex === -1 ||
			rosterColIndex === -1
		) {
			console.log(
				"Could not find required columns (FirstName, LastName, Roster) in Roster sheet!"
			);
			console.log(
				"Available columns:",
				rosterHeaderRow
					.map((col) => (col ? col.toString().trim() : ""))
					.filter((col) => col)
			);
			return;
		}

		// Now let's read data in smaller chunks to avoid the memory issue
		// We'll determine the actual data range more carefully
		console.log("=== Reading data in manageable chunks ===");

		// Start by finding the last row with data in our key columns
		const maxCol: number =
			Math.max(firstNameColIndex, lastNameColIndex, rosterColIndex) + 1;
		const lastRowRange: ExcelScript.Range | undefined = rosterSheet
			.getRange(`A:${getColumnLetter(maxCol)}`)
			.getUsedRange();

		let actualEndRow: number = 100; // Start conservative
		if (lastRowRange) {
			const lastRowAddress: string = lastRowRange.getAddress();
			console.log("Actual used range for our columns:", lastRowAddress);
			// Extract row number from address like "Roster!A1:C2569"
			const match = lastRowAddress.match(/:.*?(\d+)$/);
			if (match) {
				actualEndRow = parseInt(match[1]);
				console.log("Detected last row:", actualEndRow);
			}
		}

		// Read data in chunks of 500 rows to avoid memory issues
		const CHUNK_SIZE: number = 500;
		const rosterValues: (string | number | boolean)[][] = [];

		// Add the header row first
		rosterValues.push(rosterHeaderRow);

		for (
			let startRow = headerRowIndex + 2;
			startRow <= actualEndRow;
			startRow += CHUNK_SIZE
		) {
			const endRow: number = Math.min(startRow + CHUNK_SIZE - 1, actualEndRow);
			const chunkRange: ExcelScript.Range = rosterSheet.getRange(
				`A${startRow}:${getColumnLetter(maxCol)}${endRow}`
			);
			const chunkValues: (string | number | boolean)[][] =
				chunkRange.getValues();

			if (chunkValues) {
				rosterValues.push(...chunkValues);
				console.log(`Read rows ${startRow} to ${endRow} successfully`);
			} else {
				console.log(`Failed to read chunk ${startRow} to ${endRow}`);
				break;
			}
		}

		console.log(`Successfully read ${rosterValues.length} total rows of data`);
		console.log("=== END DIAGNOSTIC ===");

		// Filter criteria for Schedule A checking
		const scheduleATypes: Set<string> = new Set<string>([
			"Schedule A",
			"Schedule A Monthly",
			"Weekly",
			"TriWeekly",
		]);

		interface RosterEntry {
			normalizedName: string;
			rowIndex: number;
			matched: boolean;
		}

		const eligibleRosterNames: RosterEntry[] = [];
		const exactMatchMap: Map<string, number> = new Map<string, number>(); // For O(1) exact lookups

		// Process roster entries - only include Schedule A eligible entries
		for (let row: number = 1; row < rosterValues.length; row++) {
			const rosterType: string =
				rosterValues[row][rosterColIndex]?.toString().trim() || "";

			// Only process if this person is in a Schedule A eligible roster type
			if (scheduleATypes.has(rosterType)) {
				let firstName: string =
					rosterValues[row][firstNameColIndex]?.toString() || "";
				let lastName: string =
					rosterValues[row][lastNameColIndex]?.toString() || "";

				// Clean and normalize names
				firstName = cleanName(firstName);
				lastName = cleanName(lastName);

				const normalizedName: string = normalizeName(firstName, lastName);

				if (normalizedName) {
					const entryIndex: number = eligibleRosterNames.length;
					eligibleRosterNames.push({
						normalizedName: normalizedName,
						rowIndex: row,
						matched: false,
					});

					// Add to exact match map for quick lookup
					exactMatchMap.set(normalizedName, entryIndex);
				}
			}
		}

		console.log(
			`Found ${eligibleRosterNames.length} Schedule A eligible roster entries to compare against.`
		);

		// Step 2: Process ActivityReport sheet - Get Schedule A column
		const activityUsedRange: ExcelScript.Range | undefined =
			activitySheet.getUsedRange();
		if (!activityUsedRange) {
			console.log("ActivityReport sheet is empty!");
			return;
		}

		const activityValues: (string | number | boolean)[][] =
			activityUsedRange.getValues();

		if (!activityValues || activityValues.length === 0) {
			console.log("ActivityReport sheet has no data!");
			return;
		}

		const activityHeaderRow: (string | number | boolean)[] = activityValues[0];
		const scheduleAColIndex: number = activityHeaderRow.findIndex(
			(col) => col && col.toString() === "Schedule A"
		);

		if (scheduleAColIndex === -1) {
			console.log(
				"Could not find 'Schedule A' column in ActivityReport sheet!"
			);
			console.log(
				"Available columns:",
				activityHeaderRow.map((col) => (col ? col.toString() : ""))
			);
			return;
		}

		interface ActivityEntry {
			normalizedName: string;
			rowIndex: number;
			matched: boolean;
		}

		const scheduleANames: ActivityEntry[] = [];

		// Process Activity Report entries
		for (let row: number = 1; row < activityValues.length; row++) {
			let scheduledName: string =
				activityValues[row][scheduleAColIndex]?.toString() || "";

			if (scheduledName.trim()) {
				// Clean first, then normalize
				const cleanedName: string = cleanName(scheduledName);
				const normalizedName: string = normalizeActivityName(cleanedName);

				if (normalizedName) {
					scheduleANames.push({
						normalizedName: normalizedName,
						rowIndex: row,
						matched: false,
					});
				}
			}
		}

		console.log(`Found ${scheduleANames.length} Schedule A entries to match.`);

		// Step 3: Optimized matching process
		let exactMatches: number = 0;
		let fuzzyMatches: number = 0;

		// First pass: Exact matches (O(1) lookup)
		scheduleANames.forEach((activityEntry: ActivityEntry) => {
			const exactMatchIndex: number | undefined = exactMatchMap.get(
				activityEntry.normalizedName
			);
			if (exactMatchIndex !== undefined) {
				activityEntry.matched = true;
				eligibleRosterNames[exactMatchIndex].matched = true;
				exactMatches++;
			}
		});

		// Second pass: Fuzzy matching for unmatched entries
		const unmatchedActivityNames: ActivityEntry[] = scheduleANames.filter(
			(entry) => !entry.matched
		);
		const unmatchedRosterNames: RosterEntry[] = eligibleRosterNames.filter(
			(entry) => !entry.matched
		);

		console.log(
			`Exact matches: ${exactMatches}. Processing ${unmatchedActivityNames.length} unmatched activity names against ${unmatchedRosterNames.length} unmatched roster names.`
		);

		// Process in batches to avoid memory pressure
		const BATCH_SIZE: number = 50;
		for (
			let batchStart: number = 0;
			batchStart < unmatchedActivityNames.length;
			batchStart += BATCH_SIZE
		) {
			const batch: ActivityEntry[] = unmatchedActivityNames.slice(
				batchStart,
				batchStart + BATCH_SIZE
			);

			batch.forEach((activityEntry: ActivityEntry) => {
				let bestMatchScore: number = 0;
				let bestMatchIndex: number = -1;

				unmatchedRosterNames.forEach(
					(rosterEntry: RosterEntry, index: number) => {
						const similarity: number = calculateOptimizedSimilarity(
							activityEntry.normalizedName,
							rosterEntry.normalizedName,
							0.85 // 85% threshold
						);

						if (similarity > bestMatchScore) {
							bestMatchScore = similarity;
							bestMatchIndex = index;
						}
					}
				);

				// If we found a good match
				if (bestMatchScore > 0.85) {
					activityEntry.matched = true;
					unmatchedRosterNames[bestMatchIndex].matched = true;
					// Also update the original array
					const originalIndex: number = eligibleRosterNames.findIndex(
						(entry) =>
							entry.rowIndex === unmatchedRosterNames[bestMatchIndex].rowIndex
					);
					if (originalIndex !== -1) {
						eligibleRosterNames[originalIndex].matched = true;
					}
					fuzzyMatches++;
				}
			});
		}

		console.log(
			`Fuzzy matches: ${fuzzyMatches}. Total matches: ${
				exactMatches + fuzzyMatches
			}.`
		);

		// Step 4: Apply highlighting and formatting

		// Highlight unmatched Schedule A entries in light pink
		scheduleANames.forEach((entry: ActivityEntry) => {
			if (!entry.matched) {
				const excelRowNumber: number = entry.rowIndex + 1;
				const scheduleAColLetter: string = getColumnLetter(
					scheduleAColIndex + 1
				);

				// Validate the range address before using it
				if (excelRowNumber > 0 && scheduleAColLetter) {
					const range: ExcelScript.Range = activitySheet.getRange(
						`${scheduleAColLetter}${excelRowNumber}`
					);
					range.getFormat().getFill().setColor("#FFB6C1"); // Light pink
				}
			}
		});

		// Change text color to red for matched roster entries
		eligibleRosterNames.forEach((entry: RosterEntry) => {
			if (entry.matched) {
				// Calculate the actual Excel row number based on our chunked reading
				// The rowIndex refers to the position in our rosterValues array
				// We need to map this back to the actual Excel row
				const actualExcelRow: number = headerRowIndex + 1 + entry.rowIndex;
				const rosterColLetter: string = getColumnLetter(rosterColIndex + 1);

				// Validate the range address before using it
				if (actualExcelRow > 0 && rosterColLetter) {
					const range: ExcelScript.Range = rosterSheet.getRange(
						`${rosterColLetter}${actualExcelRow}`
					);
					range.getFormat().getFont().setColor("red");
				}
			}
		});

		console.log(
			`Highlighting complete. ${
				scheduleANames.length - exactMatches - fuzzyMatches
			} unmatched Schedule A entries highlighted in pink.`
		);
		console.log(
			`${
				exactMatches + fuzzyMatches
			} matched roster entries marked with red text.`
		);
	} finally {
		// Restore original calculation mode
		workbook.getApplication().setCalculationMode(originalCalculationMode);
		console.log("Script completed - calculation mode restored");
	}
}

// Helper function to clean names (remove comments and extra characters)
function cleanName(name: string): string {
	// Remove parenthetical comments first
	let cleaned: string = name.split("(")[0].trim();

	// Remove specific hyphen patterns that are likely separators/formatting
	cleaned = cleaned.replace(/ - /g, " "); // Remove " - " (space-hyphen-space)
	cleaned = cleaned.replace(/- /g, ""); // Remove "- " (hyphen-space at start or after space)
	cleaned = cleaned.replace(/ -$/g, ""); // Remove " -" (space-hyphen at end)

	return cleaned.trim();
}

// Helper function to normalize roster names (FirstName + LastName)
function normalizeName(firstName: string, lastName: string): string {
	const combined: string = (firstName + lastName).toLowerCase();
	return combined.replace(/\s+/g, "").replace(/[^a-z]/g, "");
}

// Helper function to normalize activity names
function normalizeActivityName(name: string): string {
	// Remove everything after "(" and normalize
	const cleaned: string = name.split("(")[0].trim().toLowerCase();
	return cleaned.replace(/\s+/g, "").replace(/[^a-z]/g, "");
}

// Optimized similarity calculation with early termination
function calculateOptimizedSimilarity(
	str1: string,
	str2: string,
	threshold: number = 0.85
): number {
	// Quick filters for performance
	const lengthDiff: number = Math.abs(str1.length - str2.length);
	const maxLength: number = Math.max(str1.length, str2.length);

	if (maxLength === 0) return 1.0;

	// If length difference is too large, skip expensive calculation
	if (lengthDiff > maxLength * (1 - threshold)) {
		return 0;
	}

	// First character check (common optimization for names)
	if (str1[0] !== str2[0]) {
		return 0;
	}

	// Use Jaccard similarity for quick pre-filtering
	const jaccardScore: number = jaccardSimilarity(str1, str2);
	if (jaccardScore < 0.6) {
		return 0;
	}

	// Only do expensive Levenshtein for promising candidates
	const maxDistance: number = Math.floor(maxLength * (1 - threshold));
	const distance: number = levenshteinDistanceWithLimit(
		str1,
		str2,
		maxDistance
	);

	if (distance > maxDistance) return 0;
	return (maxLength - distance) / maxLength;
}

// Fast Jaccard similarity for pre-filtering
function jaccardSimilarity(str1: string, str2: string): number {
	const set1: Set<string> = new Set<string>(str1.split(""));
	const set2: Set<string> = new Set<string>(str2.split(""));

	// Convert Sets to arrays for Office Scripts compatibility
	const arr1: string[] = Array.from(set1);
	const arr2: string[] = Array.from(set2);

	const intersection: string[] = arr1.filter((x) => set2.has(x));
	const union: string[] = [...arr1, ...arr2.filter((x) => !set1.has(x))];

	return intersection.length / union.length;
}

// Memory-optimized Levenshtein distance with early termination
function levenshteinDistanceWithLimit(
	str1: string,
	str2: string,
	maxDistance: number
): number {
	const m: number = str1.length;
	const n: number = str2.length;

	// Use rolling arrays instead of full matrix for memory efficiency
	let prev: number[] = Array(n + 1)
		.fill(0)
		.map((_, i) => i);
	let curr: number[] = Array(n + 1).fill(0);

	for (let i: number = 1; i <= m; i++) {
		curr[0] = i;
		let minInRow: number = i;

		for (let j: number = 1; j <= n; j++) {
			const cost: number = str1[i - 1] === str2[j - 1] ? 0 : 1;
			curr[j] = Math.min(
				prev[j] + 1, // Deletion
				curr[j - 1] + 1, // Insertion
				prev[j - 1] + cost // Substitution
			);
			minInRow = Math.min(minInRow, curr[j]);
		}

		// Early termination: if minimum in row exceeds limit, no valid path
		if (minInRow > maxDistance) {
			return maxDistance + 1;
		}

		// Swap arrays
		const temp: number[] = prev;
		prev = curr;
		curr = temp;
	}

	return prev[n];
}

// Helper function to convert column number to Excel column letter
function getColumnLetter(columnNumber: number): string {
	let columnLetter: string = "";
	while (columnNumber > 0) {
		const remainder: number = (columnNumber - 1) % 26;
		columnLetter = String.fromCharCode(65 + remainder) + columnLetter;
		columnNumber = Math.floor((columnNumber - 1) / 26);
	}
	return columnLetter;
}
