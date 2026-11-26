import asyncio, json, os, shutil
from playwright.async_api import async_playwright
L=json.load(open('lines.json'))
win=[(l.get('pre',l['words'][0][1]-0.3)-0.05, l['end']+0.25) for l in L]
n=len(os.listdir('allf'))
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--font-render-hinting=none','--allow-file-access-from-files'])
        pg=await b.new_page(viewport={'width':1440,'height':1080})
        await pg.goto('file:///home/claude/vid/cap/captions_built.html'); await pg.wait_for_timeout(300); await pg.evaluate('window.ready')
        for i in range(1,n+1):
            t=(i-1)/30; src=f'allf/f_{i:04d}.jpg'; dst=f'comp/f_{i:04d}.jpg'
            if any(a<=t<=e for a,e in win):
                await pg.evaluate(f"setBg('{src}')"); await pg.evaluate(f'render({t})')
                await pg.screenshot(path=dst, type='jpeg', quality=95)
            else: shutil.copy(src,dst)
        await b.close()
asyncio.run(main())
