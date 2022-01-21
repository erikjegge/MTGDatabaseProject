/****** Object:  Table [dbo].[tbl_MTGCardLibrary]    Script Date: 1/21/2022 8:27:24 AM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[tbl_MTGCardLibrary](
	[pkCard] [int] IDENTITY(1,1) NOT NULL,
	[cardName] [varchar](max) NULL,
	[isEnabled] [bit] NOT NULL,
	[color] [varchar](5) NULL,
	[type] [varchar](250) NULL,
	[set] [varchar](5) NULL,
	[filepath] [varchar](max) NULL,
	[manaCost] [varchar](100) NULL,
	[isFoil] [bit] NULL,
	[boxCode] [int] NULL,
	[cardID] [varchar](250) NULL,
 CONSTRAINT [PK_tbl_MTGCardLibrary] PRIMARY KEY CLUSTERED 
(
	[pkCard] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
ALTER TABLE [dbo].[tbl_MTGCardLibrary] ADD  DEFAULT ((1)) FOR [isEnabled]
GO
