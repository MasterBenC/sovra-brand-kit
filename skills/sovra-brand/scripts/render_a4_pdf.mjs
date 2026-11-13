// Run after installing Playwright in this package or making it available to Node.
import {pathToFileURL} from 'node:url';
import path from 'node:path';import fs from 'node:fs/promises';
const args=process.argv.slice(2),input=args[0];const val=(flag)=>{const i=args.indexOf(flag);return i<0?undefined:args[i+1]};
if(!input||!val('--pdf'))throw new Error('Usage: node scripts/render_pdf.mjs input.html --pdf output.pdf [--preview-dir previews]');
let chromium;try{({chromium}=await import('playwright'));}catch{throw new Error('Playwright is required. Install it in this package; see docs/运行与字体.md.');}
const options={headless:true};if(process.env.CHROME_PATH)options.executablePath=process.env.CHROME_PATH;
const browser=await chromium.launch(options);
try{
 const page=await browser.newPage({viewport:{width:1000,height:1300},deviceScaleFactor:1.5});await page.goto(pathToFileURL(path.resolve(input)).href);await page.evaluate(()=>document.fonts.ready);
 const checks=await page.locator('.page').evaluateAll(pages=>pages.map((p,i)=>{const box=p.getBoundingClientRect(),footer=p.querySelector('footer')?.getBoundingClientRect();const targets=[...p.querySelectorAll('h1,h2,.lead,.statement,.meeting-note,section,.execution-note')];const violations=targets.flatMap(el=>{const r=el.getBoundingClientRect();return r.left<box.left||r.right>box.right||r.bottom>(footer?.top??box.bottom)?[el.textContent.slice(0,60)]:[]});for(const el of p.querySelectorAll('h1 span'))if(el.scrollWidth>el.clientWidth+1)violations.push('Title line overflow');return {page:i+1,violations};}));
 if(checks.some(x=>x.violations.length)){console.error(JSON.stringify(checks,null,2));throw new Error('Layout overflow: shorten/restructure content or add pages before exporting.');}
 const pdf=path.resolve(val('--pdf'));await fs.mkdir(path.dirname(pdf),{recursive:true});await page.pdf({path:pdf,printBackground:true,preferCSSPageSize:true});
 const preview=val('--preview-dir');if(preview){await fs.mkdir(preview,{recursive:true});for(let i=0;i<await page.locator('.page').count();i++)await page.locator('.page').nth(i).screenshot({path:path.join(preview,`page-${String(i+1).padStart(2,'0')}.png`)});await fs.writeFile(path.join(preview,'layout-check.json'),JSON.stringify(checks,null,2));}
 console.log(`Exported ${checks.length} pages: ${pdf}`);
}finally{await browser.close();}
