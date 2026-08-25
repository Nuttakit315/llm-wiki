# สถาปัตยกรรม Persistent Knowledge Base สำหรับ AI Agents

ระบบสถาปัตยกรรม Persistent Knowledge Base ถูกคิดค้นขึ้นเพื่อให้ AI Agent มีความจำระยะยาว (Long-Term Memory) และสามารถสะสมองค์ความรู้ได้อย่างต่อเนื่อง โดยแนวคิดนี้ใช้การจัดเก็บข้อมูลแบบ 3 ชั้น (Raw, Wiki, Graph)

## องค์ประกอบสำคัญ
1. **The Wiki Layer**: เป็น Living Document ที่ AI สามารถอัปเดตแบบ Evergreen Note
2. **Knowledge Graph**: แผนผังความสัมพันธ์ที่เชื่อมโยงด้วย Wikilinks
3. **Deterministic Linter**: ระบบตรวจสอบความถูกต้องของโครงข่ายเพื่อป้องกัน Broken Links
