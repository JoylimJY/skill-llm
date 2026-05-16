/**
 * 精简版机关公文模板
 * 只需修改 CONFIG 和 CONTENTS 即可快速生成公文
 */

const {
  Document, Paragraph, TextRun, Packer, Alignment, Footer, PageNumber
} = require('docx');
const fs = require('fs');

// ============ 配置区 ============
const CONFIG = {
  docNumber: "机字〔2025〕1号",  // 发文字号
  title: "关于XXX的通知",         // 公文标题
  recipients: "各部门：",          // 主送机关
  author: "XXX办公室",            // 署名
  date: "2025年1月1日",           // 日期
  attachments: [],                // 附件列表
  output: "公文.docx"             // 输出文件
};

// ============ 正文内容 ============
const CONTENTS = [
  // { type: "normal"|"h1"|"h2"|"blank", text: "..." }
  { type: "normal", text: "根据上级精神，现就XXX工作通知如下：" },
  { type: "h1", text: "一、工作目标" },
  { type: "normal", text: "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX。" },
  { type: "h1", text: "二、工作要求" },
  { type: "normal", text: "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX。" },
  { type: "normal", text: "以上通知，请遵照执行。" }
];

// ============ 样式 ============
const S = {
  docNumber: { font: "仿宋_GB2312", size: 32, align: Alignment.LEFT },
  title: { font: "方正小标宋简体", size: 44, bold: true, align: Alignment.CENTER },
  normal: { font: "仿宋_GB2312", size: 32, firstLine: 640, line: 570 },
  h1: { font: "黑体", size: 32, bold: true, firstLine: 640 },
  h2: { font: "楷体_GB2312", size: 32, bold: true, firstLine: 640 }
};

function p(text, style) {
  return new Paragraph({
    children: [new TextRun({ text, font: style.font, size: style.size, bold: style.bold, language: "zh-CN" })],
    alignment: style.align || Alignment.LEFT,
    spacing: { line: style.line || 0, lineRule: style.line ? "exact" : undefined, after: 200 },
    indent: { firstLine: style.firstLine || 0 }
  });
}

// ============ 生成 ============
async function main() {
  const children = [];
  if (CONFIG.docNumber) children.push(p(CONFIG.docNumber, S.docNumber));
  children.push(p(CONFIG.title, S.title));
  if (CONFIG.recipients) children.push(p(CONFIG.recipients, { ...S.normal, firstLine: 0 }));
  CONTENTS.forEach(c => {
    if (c.type === "blank") children.push(new Paragraph({ children: [new TextRun({ text: "" })] }));
    else if (c.type === "h1") children.push(p(c.text, S.h1));
    else if (c.type === "h2") children.push(p(c.text, S.h2));
    else children.push(p(c.text, S.normal));
  });
  if (CONFIG.author) children.push(p(CONFIG.author, { ...S.normal, align: Alignment.RIGHT, firstLine: 0 }));
  if (CONFIG.date) children.push(p(CONFIG.date, { ...S.normal, align: Alignment.RIGHT, firstLine: 0 }));

  const doc = new Document({
    sections: [{
      properties: { page: { margin: { top: 2098, bottom: 1984, left: 1587, right: 1474 } } },
      footers: { default: new Footer({ children: [new Paragraph({ alignment: Alignment.RIGHT, children: [new TextRun({ children: ["- ", PageNumber.CURRENT, " -"], font: "宋体", size: 24 })] })] }) },
      children
    }]
  });
  fs.writeFileSync(CONFIG.output, await Packer.toBuffer(doc));
  console.log("OK:", CONFIG.output);
}
main().catch(console.error);
