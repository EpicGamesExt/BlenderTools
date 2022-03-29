const {description, repository, name} = require('../../package')

module.exports = {
    /**
     * Ref：https://v1.vuepress.vuejs.org/config/#title
     */
    title: 'UE to Rigify',
    base: process.env.NODE_ENV !== 'development' ? `/${name}/ue2rigify/` : '/',
    /**
     * Ref：https://v1.vuepress.vuejs.org/config/#description
     */
    description: description,

    /**
     * Extra tags to be injected to the page HTML `<head>`
     *
     * ref：https://v1.vuepress.vuejs.org/config/#head
     */
    head: [
        ['meta', {name: 'theme-color', content: '#3eaf7c'}],
        ['meta', {name: 'apple-mobile-web-app-capable', content: 'yes'}],
        ['meta', {name: 'apple-mobile-web-app-status-bar-style', content: 'black'}]
    ],

    /**
     * Theme configuration, here is the default theme configuration for VuePress.
     *
     * ref：https://v1.vuepress.vuejs.org/theme/default-theme-config.html
     */
    themeConfig: {
        repo: repository,
        docsDir: 'docs/ue2rigify',
        editLinks: true,
        editLinkText: 'Help us improve this page!',
        lastUpdated: false,
        nav: [
            {
                text: 'Home',
                link: '/',
            }
        ],
        sidebar: {
            '/': [
                {
                    title: 'Introduction',
                    collapsable: false,
                    children: [
                        'introduction/quickstart'
                    ]
                },
                {
                    title: 'Concepts',
                    collapsable: false,
                    children: [
                        'concepts/modes',
                        'concepts/templates'
                    ]
                },
                {
                    title: 'Usage',
                    collapsable: false,
                    children: [
                        'usage/animation',
                        'usage/new-template-example'
                    ]
                },
                {
                    title: 'Advanced',
                    collapsable: false,
                    children: [
                        'advanced/relink-constraints'
                    ]
                },
                {
                    title: 'Trouble Shooting',
                    collapsable: false,
                    children: [
                        'trouble-shooting/faq',
                        'trouble-shooting/errors',
                    ]
                }
            ],
        }
    },

    /**
     * Apply plugins，ref：https://v1.vuepress.vuejs.org/zh/plugin/
     */
    plugins: [
        '@vuepress/plugin-back-to-top',
        '@vuepress/plugin-medium-zoom'
    ]
}
