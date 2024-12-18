/****** Object:  Table [dbo].[tbl_MTGSetLibrary]    Script Date: 12/8/2024 12:01:49 PM ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[tbl_MTGSetLibrary](
	[setPK] [int] IDENTITY(1,1) NOT NULL,
	[setName] [varchar](200) NULL,
	[setCode] [varchar](5) NULL,
 CONSTRAINT [PK_tbl_MTGSetLibrary] PRIMARY KEY CLUSTERED 
(
	[setPK] ASC
)WITH (STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, OPTIMIZE_FOR_SEQUENTIAL_KEY = OFF) ON [PRIMARY]
) ON [PRIMARY]
GO
