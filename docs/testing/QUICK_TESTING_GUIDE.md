# 🚀 Quick Testing Guide

**URL:** http://localhost:8000/search
**Time:** 15-20 minutes for basic testing

---

## ⚡ Quick Test Sequence (5 Minutes)

### 1. Query Suggestions ✨
1. Click in the search box
2. Type: "rna"
3. **EXPECT:** Dropdown appears with suggestions like "RNA-seq in [organism]"
4. Click a suggestion
5. **EXPECT:** Search box fills with the suggestion text

### 2. Example Chips 💊
1. Look below the search box
2. **EXPECT:** 5 blue chip buttons
3. Click "breast cancer RNA-seq"
4. **EXPECT:** Search executes automatically, results appear

### 3. Search History 📜
1. Click "📜 History" button (top-right corner)
2. **EXPECT:** Panel slides in from right
3. **EXPECT:** Your recent search is listed
4. Click the history item
5. **EXPECT:** Search runs again

### 4. Query Validation ✅
1. Clear the search box
2. Type: "ab" (2 chars)
3. **EXPECT:** Red error message below search box
4. Type: "cancer" (single word)
5. **EXPECT:** Yellow warning message
6. Type: "breast cancer study"
7. **EXPECT:** Green success message

### 5. Results & Visualization 📊
1. Perform a search
2. **EXPECT:** Results appear in cards
3. Click "📊 Visualize" button
4. **EXPECT:** Charts appear showing study types, organisms, sample sizes

---

## 🐛 What to Look For

### Visual Issues
- [ ] Text cut off or overlapping
- [ ] Buttons not clickable
- [ ] Colors not contrasting enough
- [ ] Layouts broken on smaller window

### Functional Issues
- [ ] Features not responding to clicks
- [ ] Searches not returning results
- [ ] History not saving
- [ ] Suggestions not appearing

### Console Errors
1. Open DevTools (F12 or Cmd+Option+I)
2. Go to Console tab
3. **LOOK FOR:** Red errors (warnings are OK)
4. **REPORT:** Any errors you see

---

## 📸 What to Screenshot

If you find issues:
1. Take a screenshot of the visual problem
2. Note what you clicked to cause it
3. Copy any console errors

---

## ✅ If Everything Works

If all 5 quick tests pass:
1. ✅ Task 3 features are working!
2. ✅ Ready for production deployment
3. ✅ Can proceed with cleanup tasks

---

## 🚨 If Something Breaks

Tell me:
1. **What you did:** "I clicked [button]"
2. **What happened:** "The page froze"
3. **What you expected:** "Results should appear"
4. **Console errors:** Copy any red text from console

I'll fix it immediately!

---

## 🎯 Success Criteria

**Minimum for Production:**
- Search works (gets results)
- No JavaScript errors
- Page doesn't crash
- Mobile-friendly layout

**Ideal State:**
- All 5 quick tests pass
- Looks professional
- Fast and responsive
- No bugs found

---

**Ready?** Open http://localhost:8000/search and start testing! 🚀
