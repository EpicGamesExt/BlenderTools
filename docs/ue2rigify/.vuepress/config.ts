const {description, repository, name} = require('../../package')
import { defaultTheme } from '@vuepress/theme-default'
import { defineUserConfig } from '@vuepress/cli'
import { palettePlugin } from '@vuepress/plugin-palette'
// @ts-ignore
import { googleAnalyticsPlugin } from '@vuepress/plugin-google-analytics'


export default defineUserConfig({
    title: 'UE to Rigify',
    description: description,
    // @ts-ignore
    base: process.env.PROD === '1' ? `/${name}/` : '/',

    theme: defaultTheme({
        repo: repository,
        docsDir: 'docs/ue2rigify',
        editLinkText: 'Help us improve this page!',
        lastUpdated: false,

        navbar: [
            {
                text: 'Home',
                link: process.env.PROD === '1' ? 'https://epicgames.github.io/BlenderTools/' : '/',
                target:'_self',
                // rel:false
            }
        ],
        sidebar: {
            '/': [
                {
                    text: 'Introduction',
                    children: [
                        '/introduction/quickstart'
                    ]
                },
                {
                    text: 'Concepts',
                    children: [
                        '/concepts/modes',
                        '/concepts/templates'
                    ]
                },
                {
                    text: 'Usage',
                    children: [
                        '/usage/animation',
                        '/usage/new-template-example'
                    ]
                },
                {
                    text: 'Advanced',
                    children: [
                        '/advanced/relink-constraints'
                    ]
                },
                {
                    text: 'Extras',
                    children: [
                        '/extras/community-templates'
                    ]
                },
                {
                    text: 'Trouble Shooting',
                    children: [
                        '/trouble-shooting/faq',
                        '/trouble-shooting/errors',
                    ]
                }
            ],
        }
    }),
    plugins: [
        palettePlugin({preset: 'sass'}),
        googleAnalyticsPlugin({id: process.env.GA_ID})
    ]
})

