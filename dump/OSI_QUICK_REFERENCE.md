# Quick OSI Scoring Reference

## OSI Score Calculation

The Onychomycosis Severity Index combines two factors:

### Factor 1: Area Score (A)
Based on percentage of nail plate affected:

| Affected % | Score |
|-----------|-------|
| 0%        | 0     |
| 1-10%     | 1     |
| 11-25%    | 2     |
| 26-50%    | 3     |
| 51-75%    | 4     |
| 76-100%   | 5     |

### Factor 2: Proximity Score (P)
Based on location of infection:

| Location                          | Score |
|-----------------------------------|-------|
| Distal quarter (tip)              | 1     |
| Second quarter                    | 2     |
| Third quarter                     | 3     |
| Proximal quarter (near base)      | 4     |
| Matrix involvement (lunula/fold)  | 5     |

### Final OSI Score
**OSI = Area Score × Proximity Score**

**Range: 0-25**

## Severity Interpretation

| Score | Severity                        |
|-------|---------------------------------|
| 0     | Clinically Cured / No involvement |
| 1-5   | Mild                            |
| 6-15  | Moderate                        |
| 16-25 | Severe                          |

## Scoring Examples

### Example 1: Mild Infection
- 5% of nail affected → Area Score = 1
- Distal quarter only → Proximity Score = 1
- **OSI = 1 × 1 = 1 (Mild)**

### Example 2: Moderate Infection
- 40% of nail affected → Area Score = 3
- Third quarter → Proximity Score = 3
- **OSI = 3 × 3 = 9 (Moderate)**

### Example 3: Severe Infection
- 80% of nail affected → Area Score = 5
- Proximal quarter (base) → Proximity Score = 4
- **OSI = 5 × 4 = 20 (Severe)**

### Example 4: Matrix Involvement
- 50% of nail affected → Area Score = 3
- Matrix involvement → Proximity Score = 5
- **OSI = 3 × 5 = 15 (Moderate)**
  
*Note: Matrix involvement (score 5) significantly increases severity*

## Clinical Significance

### Mild (1-5)
- Limited to distal portion
- Good prognosis with treatment
- Often topical therapy sufficient

### Moderate (6-15)
- May involve proximal areas
- Requires systemic therapy
- Longer treatment duration

### Severe (16-25)
- Extensive or proximal involvement
- Requires aggressive treatment
- Higher risk of spread

## Key Clinical Notes

1. **Proximity is critical**: A small infection near the matrix (score 5) can be as severe as a larger distal infection (score 5)

2. **No multiplicative ceiling**: Unlike some systems, OSI allows up to 5 × 5 = 25, reflecting severe cases

3. **Grid-based assessment**: The 4×5 grid helps ensure consistent measurement across different evaluators

4. **Progressive monitoring**: Serial OSI measurements track treatment effectiveness

## Usage in MycoScan

MycoScan automatically:
1. Detects nail boundaries
2. Identifies infected areas (fungi mask)
3. Calculates infection percentage
4. Determines infection location
5. Applies OSI formula
6. Displays color-coded result:
   - 🟢 Green = Mild/Cured
   - 🔵 Blue = Mild
   - 🟠 Amber = Moderate
   - 🔴 Red = Severe
