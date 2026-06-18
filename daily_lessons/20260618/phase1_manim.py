from manim import *
import numpy as np
from utils.data_generator import generate_data


class KernelTrick3D(ThreeDScene):
    def construct(self):
        self.set_camera_orientation(phi=65 * DEGREES, theta=-70 * DEGREES)

        axes1 = ThreeDAxes(
            x_range=[-1.5, 1.5, 0.5],
            y_range=[-1.5, 1.5, 0.5],
            z_range=[0, 2.5, 0.5],
            x_length=3.2,
            y_length=3.2,
            z_length=2.2,
        ).shift(LEFT * 4.6)

        axes2 = ThreeDAxes(
            x_range=[-1.5, 1.5, 0.5],
            y_range=[-1.5, 1.5, 0.5],
            z_range=[0, 2.5, 0.5],
            x_length=3.2,
            y_length=3.2,
            z_length=2.2,
        )

        axes3 = ThreeDAxes(
            x_range=[-1.5, 1.5, 0.5],
            y_range=[-1.5, 1.5, 0.5],
            z_range=[0, 2.5, 0.5],
            x_length=3.2,
            y_length=3.2,
            z_length=2.2,
        ).shift(RIGHT * 4.6)

        self.add(axes1, axes2, axes3)

        t1 = Text("1. 2D Data", font_size=16).to_edge(UP).shift(LEFT * 4.6 + DOWN * 0.5)
        t2 = MathTex(r"2.\text{ Lift to 3D }(z = x^2 + y^2)", font_size=18).to_edge(UP).shift(DOWN * 0.5)
        t3 = MathTex(r"3.\text{ Insert Hyperplane }(z = c)", font_size=18).to_edge(UP).shift(RIGHT * 4.6 + DOWN * 0.5)

        self.add_fixed_in_frame_mobjects(t1, t2, t3)

        X, y = generate_data(
            n_samples=80, noise=0.05, seed=42, dataset_type="Concentric Circles"
        )
        color_map = {0: "#4C9BE8", 1: "#F97316"}
        colors = [color_map[val] for val in y]

        dots1 = VGroup()
        for pt, col in zip(X, colors):
            dot = Dot3D(point=axes1.c2p(pt[0], pt[1], 0), color=col, radius=0.05)
            dots1.add(dot)
        self.play(FadeIn(dots1))

        dots2 = VGroup()
        for pt, col in zip(X, colors):
            dot = Dot3D(point=axes2.c2p(pt[0], pt[1], 0), color=col, radius=0.05)
            dot.x_coord = pt[0]
            dot.y_coord = pt[1]
            dots2.add(dot)
        self.add(dots2)

        tracker = ValueTracker(0.0)
        for dot in dots2:
            dot.add_updater(
                lambda d: d.move_to(
                    axes2.c2p(
                        d.x_coord,
                        d.y_coord,
                        tracker.get_value() * (d.x_coord**2 + d.y_coord**2),
                    )
                )
            )

        paraboloid2 = Surface(
            lambda u, v: axes2.c2p(u, v, u**2 + v**2),
            u_range=[-1.2, 1.2],
            v_range=[-1.2, 1.2],
            fill_opacity=0.15,
            color=PURPLE,
            resolution=(12, 12),
        )

        self.play(
            tracker.animate.set_value(1.0), FadeIn(paraboloid2), run_time=3
        )
        self.wait(0.5)

        dots3 = VGroup()
        for pt, col in zip(X, colors):
            dot = Dot3D(
                point=axes3.c2p(pt[0], pt[1], pt[0] ** 2 + pt[1] ** 2),
                color=col,
                radius=0.05,
            )
            dots3.add(dot)

        paraboloid3 = Surface(
            lambda u, v: axes3.c2p(u, v, u**2 + v**2),
            u_range=[-1.2, 1.2],
            v_range=[-1.2, 1.2],
            fill_opacity=0.15,
            color=PURPLE,
            resolution=(12, 12),
        )

        p1 = axes3.c2p(-1.2, -1.2, 0.5)
        p2 = axes3.c2p(1.2, -1.2, 0.5)
        p3 = axes3.c2p(1.2, 1.2, 0.5)
        p4 = axes3.c2p(-1.2, 1.2, 0.5)
        plane = Polygon(
            p1,
            p2,
            p3,
            p4,
            fill_opacity=0.3,
            fill_color=GREEN,
            stroke_color=GREEN_A,
            stroke_width=1,
        )

        label_zc = MathTex("z = c", font_size=16).move_to(
            axes3.c2p(1.3, 0.0, 0.5)
        )

        self.play(
            FadeIn(dots3),
            FadeIn(paraboloid3),
            FadeIn(plane),
            FadeIn(label_zc),
            run_time=2,
        )
        self.wait(1)

        self.begin_ambient_camera_rotation(rate=0.08)
        self.wait(6)
        self.stop_ambient_camera_rotation()
        self.wait(1)


if __name__ == "__main__":
    import os

    os.system("manim -qh phase1_manim.py KernelTrick3D")
