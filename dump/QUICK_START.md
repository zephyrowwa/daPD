# OSI Grading - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### What You Just Got

Your MycoScan app now automatically:
1. **Detects** nails with YOLO
2. **Segments** nail and infection areas
3. **Grades** severity with OSI score (0-25)
4. **Visualizes** with 4×5 grid overlay
5. **Displays** color-coded results

### How to Use It

#### Step 1: Capture an Image
- Open MycoScan
- Click "Start Scan"
- Use camera to capture nail

#### Step 2: View Results
- Grid overlay automatically appears
- OSI score shows on result card
- Severity displayed with color

#### Step 3: Understand the Score
```
OSI Score = Area Score × Proximity Score

Score Ranges:
  0      = Clinically Cured (🟢 Green)
  1-5    = Mild (🔵 Blue)
  6-15   = Moderate (🟠 Amber)
  16-25  = Severe (🔴 Red)
```

### Visual Example

#### Result Card Layout
```
┌─────────────────────┐
│   [GRID IMAGE]      │  ← 4×5 grid overlay
│   with red spots    │
├─────────────────────┤
│ #1 | 0.95           │
├─────────────────────┤
│ 📊 OSI: 9/25        │
│ 🟠 Moderate         │
│ 📏 Area: 40%        │
└─────────────────────┘
```

#### What the Grid Shows
- **Green lines** = Grid divisions
- **Red areas** = Infection
- **White areas** = Healthy nail
- **5 rows** = From tip to base
- **4 columns** = Lateral to medial

## 📊 Score Cheat Sheet

### By Infection Size
| Size | Area Score |
|------|-----------|
| None | 0 |
| 1-10% | 1 |
| 11-25% | 2 |
| 26-50% | 3 |
| 51-75% | 4 |
| 76-100% | 5 |

### By Infection Location
| Location | Proximity | Score Factor |
|----------|-----------|--------------|
| Tip (distal) | 1 | Least severe |
| Second | 2 | ↑ |
| Middle | 3 | ↑ |
| Base (proximal) | 4 | ↑ |
| Root (matrix) | 5 | **Most severe** |

### Calculate Your Score

**Example 1: Small tip infection**
- Area: 8% → Score = 1
- Location: Tip → Multiplier = 1
- OSI = 1 × 1 = **1 (Mild)** ✓

**Example 2: Moderate spread**
- Area: 40% → Score = 3
- Location: Middle → Multiplier = 3
- OSI = 3 × 3 = **9 (Moderate)** ✓

**Example 3: Severe base infection**
- Area: 80% → Score = 5
- Location: Base → Multiplier = 4
- OSI = 5 × 4 = **20 (Severe)** ✓

## 🔍 Reading Your Results

### Green Badge (Score 0)
```
✅ CLINICALLY CURED
No infection detected
Continue prevention measures
```

### Blue Badge (Score 1-5)
```
ℹ️ MILD
Limited infection
Topical treatment recommended
Good prognosis
```

### Orange Badge (Score 6-15)
```
⚠️ MODERATE  
Significant infection
Consider systemic therapy
Regular monitoring
```

### Red Badge (Score 16-25)
```
🔴 SEVERE
Extensive infection
Immediate treatment needed
Close follow-up required
```

## 📈 Understanding the Grid

The nail is divided into a **4×5 grid**:

```
Tip
┌──┬──┬──┬──┐
├──┼──┼──┼──┤  5 rows
├──┼──┼──┼──┤  (Tip to Base)
├──┼──┼──┼──┤
│4 columns  │
│(L to M)   │
└──┴──┴──┴──┘
Base
```

**Rows** (0-4): From distal (tip) to proximal (base/matrix)
**Columns** (0-3): From lateral (left) to medial (right)

Red cells = Infected areas
Green grid = Normal nail

## 🎯 What the System Does Automatically

```
You capture photo
         ↓
System detects nails (YOLO)
         ↓
System segments nail + infection
         ↓
System creates 4×5 grid overlay
         ↓
System calculates:
  - Area percentage
  - Infection location
  - OSI Score (0-25)
  - Severity class
         ↓
Results display with color coding
```

**All automatic - no manual input needed!**

## 💾 Saving Results

### Current Workflow
- Results display automatically
- Can save to database with "Save Result" button
- Takes patient name as input

### Future Options (Coming Soon)
- Export grid images with overlays
- Track scores over time
- Generate medical reports
- Compare treatment progress

## 🧪 Quick Test

To verify everything works:

1. Open MycoScan
2. Go to scan page
3. Capture test image
4. Check results:
   - [ ] Grid appears
   - [ ] OSI score shows (0-25)
   - [ ] Severity color displays
   - [ ] Percentage shows

If all checks pass ✓ = System is working!

## ❓ Common Questions

### Q: How is the score calculated?
**A**: OSI = (Area Score 0-5) × (Location Score 1-5) = 0-25

### Q: What makes it "Severe"?
**A**: Score 16-25. Usually means large infection or near base/matrix.

### Q: Can the grid cells tell me which areas are infected?
**A**: Yes! Red cells show exactly which 4×5 cells have infection.

### Q: Does it save the grid image?
**A**: Currently shows in results. Can be extended to save to database.

### Q: How accurate is the automated grading?
**A**: Based on YOLO segmentation accuracy. Good for:
- Consistent measurement
- Tracking over time
- Standardized comparison

### Q: Can I adjust the grid size?
**A**: Grid is 4×5 (standard). Can be modified in code if needed.

## 🚨 Troubleshooting

### Grid doesn't show
→ Check that segmentation detects infection correctly

### Score seems wrong
→ Verify segmentation masks include both nail and fungi

### No color on result card
→ Check severity mapping in result_view.py

### Slow processing
→ Normal first run. Should be < 5 seconds per nail.

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| **OSI_QUICK_REFERENCE.md** | Score lookup tables |
| **OSI_GRADING_README.md** | Detailed technical docs |
| **OSI_GRID_VISUALIZATION_GUIDE.md** | Grid layout & interpretation |
| **OSI_IMPLEMENTATION_SUMMARY.md** | Complete overview |
| **OSI_TEST_EXAMPLES.py** | Code examples |

## 🎓 Learning Path

### Beginner (5 min)
1. Read: This quick start guide
2. Do: Capture one test scan
3. Understand: Basic OSI scoring

### Intermediate (15 min)
1. Read: OSI_QUICK_REFERENCE.md
2. Read: OSI_GRID_VISUALIZATION_GUIDE.md
3. Study: Your results carefully

### Advanced (30 min)
1. Read: OSI_GRADING_README.md
2. Read: analysis/osi_grading.py code
3. Explore: Test examples

### Expert (1 hour)
1. Study: Complete architecture
2. Review: Integration points
3. Plan: Custom enhancements

## 🚀 Next Steps

### Immediate
- [ ] Run the app with test scan
- [ ] Verify grid appears
- [ ] Check OSI scores
- [ ] Confirm color coding

### Short Term (Optional)
- [ ] Try multiple scans
- [ ] Test edge cases
- [ ] Review console logs
- [ ] Compare with manual scoring

### Long Term
- [ ] Integrate with database
- [ ] Generate reports
- [ ] Track patient progress
- [ ] Build analytics

## 🎯 Key Takeaways

✅ **Automatic**: No manual input needed
✅ **Fast**: < 5 seconds per nail
✅ **Standardized**: Same formula every time
✅ **Visual**: Grid overlay shows exactly what's affected
✅ **Color-coded**: Red=bad, Green=good
✅ **Scalable**: Works with multiple nails

---

**Ready to get started?** Just run the app and capture a scan!

For more details, see the other documentation files.
