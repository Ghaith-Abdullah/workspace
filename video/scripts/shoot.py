import sys, json, asyncio
from playwright.async_api import async_playwright
html=open('desktop.html').read().replace('DATA_JSON', open('data.json').read())
open('built.html','w').write(html)
async def main(mode, times, out):
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--font-render-hinting=none'])
        if mode=='tex':
            pg=await b.new_page(viewport={'width':1512,'height':982}, device_scale_factor=2)
        else:
            pg=await b.new_page(viewport={'width':1440,'height':1080})
        await pg.goto('file:///home/claude/vid/ui/built.html'); await pg.wait_for_timeout(400)
        if mode=='tex': await pg.evaluate('setTex()')
        for i,t in enumerate(times):
            await pg.evaluate(f'render({t})')
            await pg.screenshot(path=out.format(i=i,t=t), type='jpeg', quality=92)
        await b.close()
mode=sys.argv[1]; out=sys.argv[2]; times=[float(x) for x in sys.argv[3:]]
asyncio.run(main(mode,times,out))
