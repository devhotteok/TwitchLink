from PyQt6 import QtGui


class Palette:
    LIGHT = {
        QtGui.QPalette.ColorRole.Window: {
            QtGui.QPalette.ColorGroup.Disabled: (240, 240, 240),
            QtGui.QPalette.ColorGroup.Active: (240, 240, 240),
            QtGui.QPalette.ColorGroup.Inactive: (240, 240, 240)
        },
        QtGui.QPalette.ColorRole.WindowText: {
            QtGui.QPalette.ColorGroup.Disabled: (120, 120, 120),
            QtGui.QPalette.ColorGroup.Active: (0, 0, 0),
            QtGui.QPalette.ColorGroup.Inactive: (0, 0, 0)
        },
        QtGui.QPalette.ColorRole.Base: {
            QtGui.QPalette.ColorGroup.Disabled: (240, 240, 240),
            QtGui.QPalette.ColorGroup.Active: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Inactive: (255, 255, 255)
        },
        QtGui.QPalette.ColorRole.AlternateBase: {
            QtGui.QPalette.ColorGroup.Disabled: (245, 245, 245),
            QtGui.QPalette.ColorGroup.Active: (245, 245, 245),
            QtGui.QPalette.ColorGroup.Inactive: (245, 245, 245)
        },
        QtGui.QPalette.ColorRole.ToolTipBase: {
            QtGui.QPalette.ColorGroup.Disabled: (255, 255, 220),
            QtGui.QPalette.ColorGroup.Active: (255, 255, 220),
            QtGui.QPalette.ColorGroup.Inactive: (255, 255, 220)
        },
        QtGui.QPalette.ColorRole.ToolTipText: {
            QtGui.QPalette.ColorGroup.Disabled: (0, 0, 0),
            QtGui.QPalette.ColorGroup.Active: (0, 0, 0),
            QtGui.QPalette.ColorGroup.Inactive: (0, 0, 0)
        },
        QtGui.QPalette.ColorRole.PlaceholderText: {
            QtGui.QPalette.ColorGroup.Disabled: (0, 0, 0, 128),
            QtGui.QPalette.ColorGroup.Active: (0, 0, 0, 128),
            QtGui.QPalette.ColorGroup.Inactive: (0, 0, 0, 128)
        },
        QtGui.QPalette.ColorRole.Text: {
            QtGui.QPalette.ColorGroup.Disabled: (120, 120, 120),
            QtGui.QPalette.ColorGroup.Active: (0, 0, 0),
            QtGui.QPalette.ColorGroup.Inactive: (0, 0, 0)
        },
        QtGui.QPalette.ColorRole.Button: {
            QtGui.QPalette.ColorGroup.Disabled: (240, 240, 240),
            QtGui.QPalette.ColorGroup.Active: (240, 240, 240),
            QtGui.QPalette.ColorGroup.Inactive: (240, 240, 240)
        },
        QtGui.QPalette.ColorRole.ButtonText: {
            QtGui.QPalette.ColorGroup.Disabled: (120, 120, 120),
            QtGui.QPalette.ColorGroup.Active: (0, 0, 0),
            QtGui.QPalette.ColorGroup.Inactive: (0, 0, 0)
        },
        QtGui.QPalette.ColorRole.BrightText: {
            QtGui.QPalette.ColorGroup.Disabled: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Active: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Inactive: (255, 255, 255)
        },
        QtGui.QPalette.ColorRole.Light: {
            QtGui.QPalette.ColorGroup.Disabled: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Active: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Inactive: (255, 255, 255)
        },
        QtGui.QPalette.ColorRole.Midlight: {
            QtGui.QPalette.ColorGroup.Disabled: (247, 247, 247),
            QtGui.QPalette.ColorGroup.Active: (227, 227, 227),
            QtGui.QPalette.ColorGroup.Inactive: (227, 227, 227)
        },
        QtGui.QPalette.ColorRole.Dark: {
            QtGui.QPalette.ColorGroup.Disabled: (160, 160, 160),
            QtGui.QPalette.ColorGroup.Active: (160, 160, 160),
            QtGui.QPalette.ColorGroup.Inactive: (160, 160, 160)
        },
        QtGui.QPalette.ColorRole.Mid: {
            QtGui.QPalette.ColorGroup.Disabled: (160, 160, 160),
            QtGui.QPalette.ColorGroup.Active: (160, 160, 160),
            QtGui.QPalette.ColorGroup.Inactive: (160, 160, 160)
        },
        QtGui.QPalette.ColorRole.Shadow: {
            QtGui.QPalette.ColorGroup.Disabled: (0, 0, 0),
            QtGui.QPalette.ColorGroup.Active: (105, 105, 105),
            QtGui.QPalette.ColorGroup.Inactive: (105, 105, 105)
        },
        QtGui.QPalette.ColorRole.Highlight: {
            QtGui.QPalette.ColorGroup.Disabled: (0, 120, 215),
            QtGui.QPalette.ColorGroup.Active: (0, 120, 215),
            QtGui.QPalette.ColorGroup.Inactive: (240, 240, 240)
        },
        QtGui.QPalette.ColorRole.Accent: {
            QtGui.QPalette.ColorGroup.Disabled: (120, 120, 120),
            QtGui.QPalette.ColorGroup.Active: (0, 120, 215),
            QtGui.QPalette.ColorGroup.Inactive: (240, 240, 240)
        },
        QtGui.QPalette.ColorRole.HighlightedText: {
            QtGui.QPalette.ColorGroup.Disabled: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Active: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Inactive: (0, 0, 0)
        },
        QtGui.QPalette.ColorRole.Link: {
            QtGui.QPalette.ColorGroup.Disabled: (0, 0, 255),
            QtGui.QPalette.ColorGroup.Active: (0, 120, 215),
            QtGui.QPalette.ColorGroup.Inactive: (0, 120, 215)
        },
        QtGui.QPalette.ColorRole.LinkVisited: {
            QtGui.QPalette.ColorGroup.Disabled: (255, 0, 255),
            QtGui.QPalette.ColorGroup.Active: (0, 38, 66),
            QtGui.QPalette.ColorGroup.Inactive: (0, 38, 66)
        }
    }



    DARK = {
        QtGui.QPalette.ColorRole.Window: {
            QtGui.QPalette.ColorGroup.Disabled: (60, 60, 60),
            QtGui.QPalette.ColorGroup.Active: (60, 60, 60),
            QtGui.QPalette.ColorGroup.Inactive: (60, 60, 60)
        },
        QtGui.QPalette.ColorRole.WindowText: {
            QtGui.QPalette.ColorGroup.Disabled: (157, 157, 157),
            QtGui.QPalette.ColorGroup.Active: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Inactive: (255, 255, 255)
        },
        QtGui.QPalette.ColorRole.Base: {
            QtGui.QPalette.ColorGroup.Disabled: (30, 30, 30),
            QtGui.QPalette.ColorGroup.Active: (45, 45, 45),
            QtGui.QPalette.ColorGroup.Inactive: (45, 45, 45)
        },
        QtGui.QPalette.ColorRole.AlternateBase: {
            QtGui.QPalette.ColorGroup.Disabled: (52, 52, 52),
            QtGui.QPalette.ColorGroup.Active: (0, 38, 66),
            QtGui.QPalette.ColorGroup.Inactive: (0, 38, 66)
        },
        QtGui.QPalette.ColorRole.ToolTipBase: {
            QtGui.QPalette.ColorGroup.Disabled: (255, 255, 220),
            QtGui.QPalette.ColorGroup.Active: (60, 60, 60),
            QtGui.QPalette.ColorGroup.Inactive: (60, 60, 60)
        },
        QtGui.QPalette.ColorRole.ToolTipText: {
            QtGui.QPalette.ColorGroup.Disabled: (0, 0, 0),
            QtGui.QPalette.ColorGroup.Active: (212, 212, 212),
            QtGui.QPalette.ColorGroup.Inactive: (212, 212, 212)
        },
        QtGui.QPalette.ColorRole.PlaceholderText: {
            QtGui.QPalette.ColorGroup.Disabled: (255, 255, 255, 128),
            QtGui.QPalette.ColorGroup.Active: (255, 255, 255, 128),
            QtGui.QPalette.ColorGroup.Inactive: (255, 255, 255, 128)
        },
        QtGui.QPalette.ColorRole.Text: {
            QtGui.QPalette.ColorGroup.Disabled: (157, 157, 157),
            QtGui.QPalette.ColorGroup.Active: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Inactive: (255, 255, 255)
        },
        QtGui.QPalette.ColorRole.Button: {
            QtGui.QPalette.ColorGroup.Disabled: (60, 60, 60),
            QtGui.QPalette.ColorGroup.Active: (60, 60, 60),
            QtGui.QPalette.ColorGroup.Inactive: (60, 60, 60)
        },
        QtGui.QPalette.ColorRole.ButtonText: {
            QtGui.QPalette.ColorGroup.Disabled: (157, 157, 157),
            QtGui.QPalette.ColorGroup.Active: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Inactive: (255, 255, 255)
        },
        QtGui.QPalette.ColorRole.BrightText: {
            QtGui.QPalette.ColorGroup.Disabled: (166, 216, 255),
            QtGui.QPalette.ColorGroup.Active: (166, 216, 255),
            QtGui.QPalette.ColorGroup.Inactive: (166, 216, 255)
        },
        QtGui.QPalette.ColorRole.Light: {
            QtGui.QPalette.ColorGroup.Disabled: (120, 120, 120),
            QtGui.QPalette.ColorGroup.Active: (120, 120, 120),
            QtGui.QPalette.ColorGroup.Inactive: (120, 120, 120)
        },
        QtGui.QPalette.ColorRole.Midlight: {
            QtGui.QPalette.ColorGroup.Disabled: (90, 90, 90),
            QtGui.QPalette.ColorGroup.Active: (90, 90, 90),
            QtGui.QPalette.ColorGroup.Inactive: (90, 90, 90)
        },
        QtGui.QPalette.ColorRole.Dark: {
            QtGui.QPalette.ColorGroup.Disabled: (30, 30, 30),
            QtGui.QPalette.ColorGroup.Active: (30, 30, 30),
            QtGui.QPalette.ColorGroup.Inactive: (30, 30, 30)
        },
        QtGui.QPalette.ColorRole.Mid: {
            QtGui.QPalette.ColorGroup.Disabled: (40, 40, 40),
            QtGui.QPalette.ColorGroup.Active: (40, 40, 40),
            QtGui.QPalette.ColorGroup.Inactive: (40, 40, 40)
        },
        QtGui.QPalette.ColorRole.Shadow: {
            QtGui.QPalette.ColorGroup.Disabled: (0, 0, 0),
            QtGui.QPalette.ColorGroup.Active: (0, 0, 0),
            QtGui.QPalette.ColorGroup.Inactive: (0, 0, 0)
        },
        QtGui.QPalette.ColorRole.Highlight: {
            QtGui.QPalette.ColorGroup.Disabled: (0, 120, 215),
            QtGui.QPalette.ColorGroup.Active: (0, 120, 215),
            QtGui.QPalette.ColorGroup.Inactive: (30, 30, 30)
        },
        QtGui.QPalette.ColorRole.Accent: {
            QtGui.QPalette.ColorGroup.Disabled: (157, 157, 157),
            QtGui.QPalette.ColorGroup.Active: (0, 120, 215),
            QtGui.QPalette.ColorGroup.Inactive: (30, 30, 30)
        },
        QtGui.QPalette.ColorRole.HighlightedText: {
            QtGui.QPalette.ColorGroup.Disabled: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Active: (255, 255, 255),
            QtGui.QPalette.ColorGroup.Inactive: (255, 255, 255)
        },
        QtGui.QPalette.ColorRole.Link: {
            QtGui.QPalette.ColorGroup.Disabled: (48, 140, 198),
            QtGui.QPalette.ColorGroup.Active: (0, 120, 215),
            QtGui.QPalette.ColorGroup.Inactive: (0, 120, 215)
        },
        QtGui.QPalette.ColorRole.LinkVisited: {
            QtGui.QPalette.ColorGroup.Disabled: (255, 0, 255),
            QtGui.QPalette.ColorGroup.Active: (0, 38, 66),
            QtGui.QPalette.ColorGroup.Inactive: (0, 38, 66)
        }
    }