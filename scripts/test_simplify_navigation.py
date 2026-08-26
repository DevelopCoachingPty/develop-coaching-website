import unittest

from scripts.simplify_navigation import simplify_main_navigation


class SimplifyNavigationTests(unittest.TestCase):
    def test_uppercase_head_close_receives_navigation_styles(self):
        html = "<html><head></HEAD><body></body></html>"
        result = simplify_main_navigation(html)
        self.assertIn('id="dc-simplified-navigation"', result)
        self.assertIn("</HEAD>", result)

    def test_simplifies_desktop_and_mobile_menus_without_moving_cta(self):
        menu = """
        <ul>
          <li class="menu-item menu-item-7952"><a href="#">Trades</a>
            <ul><li class="menu-item menu-item-8893"><a href="/">Builders</a></li></ul>
          </li>
          <li class="menu-item menu-item-16753"><a href="/5-pillars-free-trainings/">Free Trainings</a></li>
          <li class="menu-item menu-item-9177"><a href="/blog/">Blog</a></li>
          <li class="menu-item menu-item-14446"><a href="/construction-podcast/">Podcast</a></li>
          <li class="menu-item menu-item-9176"><a href="/about-greg-wilkes/">My Story</a></li>
          <li class="menu-item menu-item-9179"><a href="/contact/">Contact</a></li>
        </ul>
        """
        html = '<html><head></head><body>' + menu + menu.replace("<a ", '<a tabindex="-1" ') + '<a class="cta" href="/schedule-a-call/">SCHEDULE A CALL</a></body></html>'

        result = simplify_main_navigation(html)

        self.assertNotIn(">Trades<", result)
        self.assertNotIn(">Blog<", result)
        self.assertNotIn(">Podcast<", result)
        self.assertEqual(result.count(">Free Resources<"), 2)
        self.assertEqual(result.count(">About Greg<"), 2)
        self.assertEqual(result.count("/schedule-a-call/"), 1)
        self.assertIn(">Contact<", result)
        self.assertEqual(result.count('id="dc-simplified-navigation"'), 1)
        self.assertIn("grid-template-columns: minmax(0, 1fr) auto", result)
        self.assertEqual(simplify_main_navigation(result), result)

    def test_leaves_podcast_and_blog_content_links_untouched(self):
        html = '<main><a href="/blog/">Blog</a><a href="/construction-podcast/">Podcast</a></main>'
        self.assertEqual(simplify_main_navigation(html), html)

    def test_desktop_flag_widgets_keep_their_intended_width(self):
        html = "<html><head></head><body></body></html>"
        result = simplify_main_navigation(html)
        desktop_style = result.split("@media (max-width: 767px)", 1)[0]
        mobile_style = result.split("@media (max-width: 767px)", 1)[1]

        self.assertIn(".elementor-element-760db8b", desktop_style)
        self.assertIn(".elementor-element-a45c51e", desktop_style)
        self.assertIn("flex: 0 0 60px !important", desktop_style)
        self.assertIn("width: 60px !important", desktop_style)
        self.assertIn("max-width: 60px !important", desktop_style)
        self.assertNotIn(".elementor-element-760db8b", mobile_style)
        self.assertNotIn(".elementor-element-a45c51e", mobile_style)


if __name__ == "__main__":
    unittest.main()
