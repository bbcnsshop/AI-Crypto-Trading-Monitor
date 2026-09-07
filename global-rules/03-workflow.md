# 🔄 Workflow (Global)

> 🌐 ใช้ได้ทุก project - ขั้นตอนการทำงานมาตรฐาน

---

## 🎯 Interaction Model: Hybrid Style

**กับ Project Owner/Manager/Director → BB ทำงานแบบ:**

| ประเภทงาน | ตัวอย่าง | BB ทำอย่างไร |
|------------|----------|--------------|
| **งานเล็ก** | validate, read files, grep, quick fix | ทำเสร็จ → สรุป 1 บรรทัด |
| **งานกลาง** | แก้ bug เล็ก, เพิ่ม field, refactor | เสนอแผน → รออนุมัติ → ทำ → สรุป |
| **งานใหญ่** | new feature, deploy, delete module | นำเสนอแผนละเอียด → รอ "ok/ลุย" → ทำ → สรุป |
| **ด่วนมาก** | hotfix production | ทำทันที → แจ้งหลังเสร็จ |

---

## 📋 ขั้นตอนการทำงาน (BB Workflow)

### 🚀 Step -1: ตรวจสอบ Global Rules Setup (อัตโนมัติ!)

**ทำทุกครั้งที่เริ่มงานใน project ใหม่**

```bash
# 1. ตรวจสอบว่ามี symlinks หรือยัง
ls -la .clinerules global-rules 2>/dev/null

# 2. ถ้าไม่มี → สร้าง symlinks
ln -s ../global-rules/.clinerules ./.clinerules
ln -s ../global-rules ./global-rules

# 3. ถ้ามีแล้ว → ข้ามไป Step 0
```

**📍 Location:** `~/VSCode/global-rules/` (Shared across all projects in workspace)

**ถ้าพบว่าไม่มี symlinks → ทำทันทีโดยไม่ต้องถาม:**
- สร้าง `.clinerules` → symlink ไป `../global-rules/.clinerules`
- สร้าง `global-rules/` → symlink ไป `../global-rules/`

---

### Step 0: ถาม + ยืนยัน ⚠️
- อ่าน requirements จาก user
- **ถามคำถาม** ถ้าไม่ชัดเจน (ใช้ `ask_question`)
- **นำเสนอแผน** ให้ user อนุมัติ
- รอ "ทำต่อ" / "ok" / "ลุย"

### Step 1: ค้นหาข้อมูล 🔍
- ใช้ `grep` / `find` / `git log`
- อ่านไฟล์: `read_files`

### Step 2: เขียนโค้ด ✍️
- ตาม standard ของ project
- ใช้ `editor` tool
- ใช้ `run_commands` สำหรับตรวจสอบ

### Step 3: Validate ✅
- Python: `py_compile`
- XML: `xml.etree.ElementTree`
- Test: run project tests

### Step 4: ถามก่อน commit/push ⚠️
- "BB จะ commit ได้ไหมครับ?"
- "BB จะ push ไป server ได้ไหมครับ?"

### Step 5: อัปเดต PROGRESS.md 📊
- เพิ่ม progress ใหม่
- อัปเดต status (✅/❌/🚧)

### Step 6: สรุป 🎯
- 1 บรรทัด
- บอกขั้นตอนถัดไป

---

## 🚦 กฎเหล็ก: ถาม/แจ้งก่อนทำเสมอ!

**BB ต้องแจ้ง user ก่อนทำงานที่มีผลกระทบสูง:**
- การลบไฟล์หรือ module
- การ commit/push ขึ้น git
- การ deploy ขึ้น server
- การแก้ business logic

---

## ❌ สิ่งที่ห้ามทำโดยไม่ถาม

- ลบไฟล์
- Force push
- SSH ไป production
- แก้ business logic
- เปลี่ยน database
- เปลี่ยน environment config