/****** Object:  Table [dbo].[tbl_MTGCardLibrary]    Script Date: 12/8/2024 12:01:49 PM ******/
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
	[isFoil] [bit] NOT NULL,
	[boxCode] [int] NULL,
	[cardID] [varchar](250) NULL,
	[pkCostBasisLot] [int] NULL,
	[damaged] [bit] NOT NULL,
	[soldDate] [datetime] NULL,
	[soldAmount] [money] NULL,
	[created_date] [datetime] NOT NULL,
 CONSTRAINT [PK_tbl_MTGCardLibrary_New] PRIMARY KEY CLUSTERED 
(
	[pkCard] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]
GO
ALTER TABLE [dbo].[tbl_MTGCardLibrary] ADD  DEFAULT ((1)) FOR [isEnabled]
GO
ALTER TABLE [dbo].[tbl_MTGCardLibrary] ADD  DEFAULT ((0)) FOR [isFoil]
GO
ALTER TABLE [dbo].[tbl_MTGCardLibrary] ADD  CONSTRAINT [DF_tbl_MTGCardLibrary_damaged]  DEFAULT ((0)) FOR [damaged]
GO
ALTER TABLE [dbo].[tbl_MTGCardLibrary] ADD  DEFAULT (getdate()) FOR [created_date]
GO
