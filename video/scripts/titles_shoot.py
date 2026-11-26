import sys, asyncio, json
from playwright.async_api import async_playwright
mode=sys.argv[1]; out=sys.argv[2]; times=[float(x) for x in sys.argv[3:]] if mode!='seq' else None
proj=json.load(open(sys.argv[3] if mode=='seq' else '/tmp/t4/proj.json'))
src=open('titles.html').read().replace('PROJ_THINK', json.dumps(proj['think']))
open('titles_built.html','w').write(src)
async def main():
    async with async_playwright() as p:
        b=await p.chromium.launch(executable_path='/usr/bin/google-chrome', args=['--font-render-hinting=none'])
        pg=await b.new_page(viewport={'width':1440,'height':1080})
        await pg.goto('file://'+__import__('os').path.abspath('titles_built.html')); await pg.wait_for_timeout(300); await pg.evaluate('window.ready')
        if mode=='preview':
            await pg.evaluate("document.body.classList.add('preview')")
            for t in times:
                await pg.evaluate(f'render({t})'); await pg.screenshot(path=out.format(t=t), type='jpeg', quality=90)
        else:
            for i in range(405):
                await pg.evaluate(f'render({i/30})'); await pg.screenshot(path=out.format(i=i), omit_background=True)
        await b.close()
asyncio.run(main())
