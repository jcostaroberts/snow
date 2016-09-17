# I want to know what the best early-season ski mountain is.
# Suck in the OTS data, do some processing to get cumulative
# average snowfall by five-day intervals, and plot the resorts
# against each other by cumulative snowfall at a given date.

# Get resort list
resorts <- read.csv("~/sync/Projects/snow/resort.txt", sep=" ",
                    header=F, col.names=c("resort", "state"),
                    comment.char="#")

# Read a resort's data file
read_resort_file <- function(resort) {
    filename <- paste("~/sync/Projects/snow/data/",
                      as.character(resort), "-2009-2016.csv", sep="")
    read.csv(filename)
}

# Create a resort-keyed list of data.frames
data <- lapply(resorts$resort, read_resort_file)
names(data) <- sapply(resorts$resort,
                      function(x) strsplit(as.character(x), "-")[[1]][1])

# Get the indices that correspond to a given year. 2010 incorporates
# December 2009 through April 2010.
season_index <- function(d, year) {
	which((d$year == (year-1) & (d$month %in% c( "Oct", "Nov", "Dec"))) |
          ((d$year == year) & (d$month %in% c("Jan", "Feb", "Mar", "Apr", "May"))))
     
}

# Build the seasonal totals
for (d in names(data)) {
    for (y in 2010:2016) {
        data[[d]]$season.total.inches[season_index(data[[d]], y)] <-
            cumsum(data[[d]]$new.snow.inches[season_index(data[[d]], y)])
    }
}
 
date_buckets <- c(5, 10, 15, 20, 25, 31)
months <- c("Dec", "Jan", "Feb", "Mar", "Apr")

# Get the indices corresponding to a date bucket.
date_index <- function(d, month, year, day) {
    idx <- which(d$month == month & d$year == year & d$day <= day)
    if (length(idx) == 0 & month != "Dec") {
        idx <- which(d$month == month & d$year == year)
        idx <- ifelse(length(idx) > 0, min(idx)-1, NA)
    }
    ifelse(length(idx) > 0, max(idx), NA)
}

total_inches <- function(d, idx) {
    ifelse(is.nan(idx), NA, d$season.total.inches[idx])
}
 
get_average_for_period <- function(d, dates) {
    month <- dates[2]
    day <- as.numeric(dates[1])
    # If the month is December, we can use 2009. Otherwise we
    # can't, since the 2009 numbers don't incorporate late 2008.
    yr_range <- 2010:2016
    if (month=="Dec") yr_range <- 2009:2015
    per_year_tot <- sapply(yr_range,
    function(x) total_inches(d, date_index(d, month, x, day)))
    # Median's probably best here because it throws out
    # anomalously high and low years, which could be due to bad
    # data. We don't really want to have the number thrown off by
    # huge snow years, since really beyond a certain point extra
    # snow doesn't really matter.
    median(per_year_tot, na.rm=T)
}

get_averages <- function(d) {
    date_table <- expand.grid(date_buckets, months)
    apply(date_table, 1, function(x) get_average_for_period(d, x))
}


dates <- data.frame(month=rep(months, each=6),
                    day=rep(sapply(date_buckets, function(x) floor(mean(x))),
                    times=5))
				   
# Create a data.frame with the median cumulative snowfall. Looks like this:
# month day resort1 resort2 ... resortn
snow_by_date <- cbind(dates, data.frame(lapply(data, get_averages)))

# NOTES ON HOW CRAPPY THSEE DATA ARE
# - The base pack numbers in this dataset are completely bogus*, and
#   the seasonal totals start on Jan 1, which is not bogus but is
#   wrong. So we have to use the daily snowfall data (which only
#   exist for days of snowfall), and build our own seasonal total
#   data.
#   * See, e.g., Revelstoke, 2013. The base pack on 1/9 is 24", and
#     after 2" of snow on 1/11, it jumps to 50".
# - Some of these, like Squaw, go down significantly from period to
#   period, even though these numbers are cumulative. This can happen
#   if one period (usually Dec) sees no snow and then the following
#   period sees an unusually small amount of snow. Northstar has no
#   Dec for 2011; Mammoth is just completely missing 2010.
# - Onthesnow stops getting data for some of these resorts (e.g.,
#   Jackson Hole, Whistler) after April 1, so showing no more snowfall
#   after then isn't quite right. But it is easier...


####################
#### PLOT STUFF ####
####################

maxval <- max(snow_by_date[,3:ncol(snow_by_date)])
minval <- min(snow_by_date[,3:ncol(snow_by_date)])

# Sanity check: vail/beaver, alta/snowbird, deer/park,
# squaw/northstar. The pairs are neighboring ski resorts and
# intra-pair differences should be small. I expect alta/snowbird
# > deer/park, alta/snowbird > squaw/vail, squaw > northstar.
plot(snow_by_date$vail, xlab="Date", ylab="Cumulative snowfall (in.)",
     ylim=c(minval, maxval), lwd=2, las=1, xaxt="n", type="l",
     main="Ski season snowfall (sanity check)")
axis(1, at=c(3, 9, 15, 21, 27), labels=c("Dec 15", "Jan 15", "Feb 15", "Mar 15", "Apr 15"))
lines(snow_by_date$beaver, lty=2, lwd=2)
lines(snow_by_date$alta, lwd=2, col="blue")
lines(snow_by_date$snowbird, lty=2, lwd=2, col="blue")
lines(snow_by_date$park, lwd=2, col="orange")
lines(snow_by_date$deer, lty=2, lwd=2, col="orange")
lines(snow_by_date$squaw, lwd=2, col="pink")
lines(snow_by_date$northstar, lty=2, lwd=2, col="pink")
legend("bottomright",
       legend=c("Vail", "Beaver Creek", "Alta", "Snowbird", "Park City",
                "Deer Valley", "Squaw/Alpine", "Northstar"),
       col=rep(c("black", "blue", "orange", "pink"), each=2),
       lty=rep(c(1,2), times=4), lwd=2, bty="n")


# Places of interest: revelstoke, squaw, kirkwood, vail, jackson,
# taos, whistler
plot(snow_by_date$revelstoke, xlab="Date", ylab="Cumulative snowfall (in.)",
     ylim=c(minval, maxval), lwd=2, las=1, xaxt="n", type="l",
     main="Ski season snowfall")
axis(1, at=c(3, 9, 15, 21, 27), labels=c("Dec 15", "Jan 15", "Feb 15", "Mar 15", "Apr 15"))
lines(snow_by_date$squaw, lwd=2, col="red")
lines(snow_by_date$kirkwood, lwd=2, col="blue")
lines(snow_by_date$vail, lwd=2, col="darkgreen")
lines(snow_by_date$jackson, lwd=2, col="orange")
lines(snow_by_date$taos, lwd=2, col="purple")
lines(snow_by_date$whistler, lwd=2, col="pink")
legend("bottomright",
       legend=c("Revelstoke", "Squaw", "Kirkwood", "Vail", "Jackson",
                "Taos", "Whistler"),
       col=c("black", "red", "blue", "darkgreen", "orange", "purple", "pink"),
       lwd=2, bty="n")
